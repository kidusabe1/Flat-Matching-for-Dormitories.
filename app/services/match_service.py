from datetime import datetime, timezone

from google.cloud.firestore_v1 import AsyncClient, async_transactional, AsyncTransaction

from app.middleware.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.enums import (
    LeaseTransferStatus,
    ListingType,
    MatchStatus,
    TransactionStatus,
)
from app.models.match import ContactResponse, MatchResponse
from app.state_machine.transitions import assert_transition


def _to_match_response(doc_id: str, data: dict) -> MatchResponse:
    return MatchResponse(
        id=doc_id,
        match_type=data["match_type"],
        status=data["status"],
        listing_id=data["listing_id"],
        claimant_uid=data["claimant_uid"],
        claimant_listing_id=data.get("claimant_listing_id"),
        offered_room_id=data["offered_room_id"],
        offered_room_category=data["offered_room_category"],
        offered_room_building=data["offered_room_building"],
        proposed_at=data.get("proposed_at"),
        responded_at=data.get("responded_at"),
        expires_at=data.get("expires_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


async def get_match(db: AsyncClient, match_id: str) -> MatchResponse:
    doc = await db.collection("matches").document(match_id).get()
    if not doc.exists:
        raise NotFoundError(f"Match {match_id} not found")
    return _to_match_response(doc.id, doc.to_dict())


async def get_user_matches(
    db: AsyncClient, uid: str, status: str | None = None
) -> list[MatchResponse]:
    query = db.collection("matches").where("claimant_uid", "==", uid)
    if status:
        query = query.where("status", "==", status)

    results = []
    async for doc in query.stream():
        results.append(_to_match_response(doc.id, doc.to_dict()))

    # Also find matches where user is the listing owner
    listing_query = (
        db.collection("listings")
        .where("owner_uid", "==", uid)
        .where("status", "in", ["MATCHED", "PENDING_APPROVAL", "FULLY_MATCHED"])
    )
    listing_ids = []
    async for doc in listing_query.stream():
        listing_ids.append(doc.id)

    for lid in listing_ids:
        match_query = db.collection("matches").where("listing_id", "==", lid)
        if status:
            match_query = match_query.where("status", "==", status)
        async for doc in match_query.stream():
            match_resp = _to_match_response(doc.id, doc.to_dict())
            if not any(r.id == match_resp.id for r in results):
                results.append(match_resp)

    return results


async def accept_match(
    db: AsyncClient, match_id: str, owner_uid: str
) -> MatchResponse:
    """Listing owner accepts a match proposal. Creates a transaction."""
    transaction = db.transaction()
    return await _accept_match_txn(transaction, db, match_id, owner_uid)


@async_transactional
async def _accept_match_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    match_id: str,
    owner_uid: str,
) -> MatchResponse:
    match_ref = db.collection("matches").document(match_id)
    match_snap = await match_ref.get(transaction=transaction)
    if not match_snap.exists:
        raise NotFoundError(f"Match {match_id} not found")

    match_data = match_snap.to_dict()
    if match_data["status"] != MatchStatus.PROPOSED.value:
        raise ConflictError(f"Match is in state {match_data['status']}, not PROPOSED")

    # Verify the caller owns the listing
    listing_ref = db.collection("listings").document(match_data["listing_id"])
    listing_snap = await listing_ref.get(transaction=transaction)
    if not listing_snap.exists:
        raise NotFoundError("Associated listing not found")

    listing = listing_snap.to_dict()
    if listing["owner_uid"] != owner_uid:
        raise ForbiddenError("Only the listing owner can accept matches")

    now = datetime.now(timezone.utc)

    # Update match status
    transaction.update(match_ref, {
        "status": MatchStatus.ACCEPTED.value,
        "responded_at": now,
        "updated_at": now,
        "version": match_data["version"] + 1,
    })

    # Transition listing to PENDING_APPROVAL
    assert_transition(listing["listing_type"], listing["status"], "PENDING_APPROVAL")
    transaction.update(listing_ref, {
        "status": "PENDING_APPROVAL",
        "updated_at": now,
        "version": listing["version"] + 1,
    })

    # Create a transaction record
    tx_ref = db.collection("transactions").document()
    tx_data = {
        "transaction_type": listing["listing_type"],
        "status": TransactionStatus.PENDING.value,
        "match_id": match_id,
        "from_uid": listing["owner_uid"],
        "to_uid": match_data["claimant_uid"],
        "room_id": listing["room_id"],
        "match_ids": None,
        "party_a_uid": None,
        "party_a_room_id": None,
        "party_b_uid": None,
        "party_b_room_id": None,
        "lease_start_date": listing["lease_start_date"],
        "lease_end_date": listing["lease_end_date"],
        "initiated_at": now,
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    transaction.create(tx_ref, tx_data)

    match_data["status"] = MatchStatus.ACCEPTED.value
    match_data["responded_at"] = now
    return _to_match_response(match_snap.id, match_data)


async def reject_match(
    db: AsyncClient, match_id: str, owner_uid: str
) -> MatchResponse:
    """Listing owner rejects a match. Reopens the listing."""
    transaction = db.transaction()
    return await _reject_match_txn(transaction, db, match_id, owner_uid)


@async_transactional
async def _reject_match_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    match_id: str,
    owner_uid: str,
) -> MatchResponse:
    match_ref = db.collection("matches").document(match_id)
    match_snap = await match_ref.get(transaction=transaction)
    if not match_snap.exists:
        raise NotFoundError(f"Match {match_id} not found")

    match_data = match_snap.to_dict()
    if match_data["status"] != MatchStatus.PROPOSED.value:
        raise ConflictError(f"Match is in state {match_data['status']}, not PROPOSED")

    listing_ref = db.collection("listings").document(match_data["listing_id"])
    listing_snap = await listing_ref.get(transaction=transaction)
    if not listing_snap.exists:
        raise NotFoundError("Associated listing not found")

    listing = listing_snap.to_dict()
    if listing["owner_uid"] != owner_uid:
        raise ForbiddenError("Only the listing owner can reject matches")

    now = datetime.now(timezone.utc)

    # Reject the match
    transaction.update(match_ref, {
        "status": MatchStatus.REJECTED.value,
        "responded_at": now,
        "updated_at": now,
        "version": match_data["version"] + 1,
    })

    # Reopen the listing
    assert_transition(listing["listing_type"], listing["status"], "OPEN")
    transaction.update(listing_ref, {
        "status": "OPEN",
        "updated_at": now,
        "version": listing["version"] + 1,
    })

    match_data["status"] = MatchStatus.REJECTED.value
    match_data["responded_at"] = now
    return _to_match_response(match_snap.id, match_data)


async def get_match_contact(
    db: AsyncClient, match_id: str, requester_uid: str
) -> ContactResponse:
    """Return counterparty contact info for an accepted match."""
    match_doc = await db.collection("matches").document(match_id).get()
    if not match_doc.exists:
        raise NotFoundError(f"Match {match_id} not found")

    match_data = match_doc.to_dict()

    if match_data["status"] != MatchStatus.ACCEPTED.value:
        raise ConflictError("Contact info is only available for accepted matches")

    # Determine the counterparty UID
    listing_doc = await db.collection("listings").document(match_data["listing_id"]).get()
    if not listing_doc.exists:
        raise NotFoundError("Associated listing not found")

    listing = listing_doc.to_dict()
    listing_owner_uid = listing["owner_uid"]
    claimant_uid = match_data["claimant_uid"]

    if requester_uid == listing_owner_uid:
        counterparty_uid = claimant_uid
    elif requester_uid == claimant_uid:
        counterparty_uid = listing_owner_uid
    else:
        raise ForbiddenError("You are not a party in this match")

    # Fetch counterparty's profile
    user_doc = await db.collection("users").document(counterparty_uid).get()
    if not user_doc.exists:
        raise NotFoundError("Counterparty profile not found")

    user_data = user_doc.to_dict()
    return ContactResponse(
        name=user_data["full_name"],
        phone=user_data.get("phone", ""),
    )
