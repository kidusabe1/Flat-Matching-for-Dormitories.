from datetime import datetime, date, timezone, timedelta

from google.cloud.firestore_v1 import AsyncClient, async_transactional, AsyncTransaction

from app.config import get_settings
from app.middleware.error_handler import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.enums import LeaseTransferStatus, ListingType, MatchStatus, SwapRequestStatus
from app.models.listing import LeaseTransferCreate, ListingResponse, ListingUpdate, SwapRequestCreate
from app.state_machine.transitions import assert_transition


def _to_listing_response(doc_id: str, data: dict) -> ListingResponse:
    def _to_date(val) -> date | None:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        return val

    return ListingResponse(
        id=doc_id,
        listing_type=data["listing_type"],
        status=data["status"],
        owner_uid=data["owner_uid"],
        room_id=data["room_id"],
        room_category=data["room_category"],
        room_building=data["room_building"],
        lease_start_date=_to_date(data["lease_start_date"]),
        lease_end_date=_to_date(data["lease_end_date"]),
        description=data.get("description", ""),
        asking_price=data.get("asking_price"),
        desired_categories=data.get("desired_categories"),
        desired_buildings=data.get("desired_buildings"),
        move_in_date=_to_date(data.get("move_in_date")),
        desired_min_start=_to_date(data.get("desired_min_start")),
        desired_max_end=_to_date(data.get("desired_max_end")),
        replacement_match_id=data.get("replacement_match_id"),
        target_match_id=data.get("target_match_id"),
        expires_at=data.get("expires_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


async def _check_no_active_listing(db: AsyncClient, owner_uid: str) -> None:
    """Ensure user has no active listing (OPEN or PARTIAL_MATCH)."""
    query = (
        db.collection("listings")
        .where("owner_uid", "==", owner_uid)
        .where("status", "in", ["OPEN", "PARTIAL_MATCH", "MATCHED", "FULLY_MATCHED"])
        .limit(1)
    )
    results = []
    async for doc in query.stream():
        results.append(doc)
    if results:
        raise ConflictError("You already have an active listing. Cancel it first.")


async def create_lease_transfer(
    db: AsyncClient, owner_uid: str, data: LeaseTransferCreate
) -> ListingResponse:
    await _check_no_active_listing(db, owner_uid)

    # Verify room exists
    room_doc = await db.collection("rooms").document(data.room_id).get()
    if not room_doc.exists:
        raise NotFoundError(f"Room {data.room_id} not found")
    room = room_doc.to_dict()

    if data.lease_end_date <= data.lease_start_date:
        raise BadRequestError("lease_end_date must be after lease_start_date")

    settings = get_settings()
    now = datetime.now(timezone.utc)
    doc_data = {
        "listing_type": ListingType.LEASE_TRANSFER.value,
        "status": LeaseTransferStatus.OPEN.value,
        "version": 1,
        "owner_uid": owner_uid,
        "room_id": data.room_id,
        "room_category": room["category"],
        "room_building": room["building"],
        "lease_start_date": datetime.combine(data.lease_start_date, datetime.min.time(), tzinfo=timezone.utc),
        "lease_end_date": datetime.combine(data.lease_end_date, datetime.min.time(), tzinfo=timezone.utc),
        "move_in_date": (
            datetime.combine(data.move_in_date, datetime.min.time(), tzinfo=timezone.utc)
            if data.move_in_date
            else None
        ),
        "description": data.description,
        "asking_price": data.asking_price,
        "expires_at": now + timedelta(days=settings.listing_expiry_days),
        "created_at": now,
        "updated_at": now,
    }

    _, doc_ref = await db.collection("listings").add(doc_data)
    return _to_listing_response(doc_ref.id, doc_data)


async def get_listing(db: AsyncClient, listing_id: str) -> ListingResponse:
    doc = await db.collection("listings").document(listing_id).get()
    if not doc.exists:
        raise NotFoundError(f"Listing {listing_id} not found")
    return _to_listing_response(doc.id, doc.to_dict())


async def get_user_listings(
    db: AsyncClient, owner_uid: str, status: str | None = None
) -> list[ListingResponse]:
    query = db.collection("listings").where("owner_uid", "==", owner_uid)
    if status:
        query = query.where("status", "==", status)

    results = []
    async for doc in query.stream():
        results.append(_to_listing_response(doc.id, doc.to_dict()))
    return results


async def list_listings(
    db: AsyncClient,
    listing_type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    building: str | None = None,
    limit: int = 20,
    page: int = 1,
) -> dict:
    query = db.collection("listings")

    if listing_type:
        query = query.where("listing_type", "==", listing_type)
    if status:
        query = query.where("status", "==", status)
    else:
        query = query.where("status", "==", "OPEN")
    if category:
        query = query.where("room_category", "==", category)
    if building:
        query = query.where("room_building", "==", building)

    query = query.limit(limit)

    items = []
    async for doc in query.stream():
        items.append(_to_listing_response(doc.id, doc.to_dict()))

    return {
        "items": items,
        "total": len(items),
        "page": page,
        "limit": limit,
        "has_next": len(items) == limit,
    }


async def update_listing(
    db: AsyncClient, listing_id: str, owner_uid: str, data: ListingUpdate
) -> ListingResponse:
    doc_ref = db.collection("listings").document(listing_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise NotFoundError(f"Listing {listing_id} not found")

    listing = doc.to_dict()
    if listing["owner_uid"] != owner_uid:
        raise ForbiddenError("You can only update your own listings")
    if listing["status"] != "OPEN":
        raise ConflictError("Can only update listings in OPEN status")

    updates = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if k in ("lease_start_date", "lease_end_date", "move_in_date"):
                updates[k] = datetime.combine(v, datetime.min.time(), tzinfo=timezone.utc)
            else:
                updates[k] = v
    updates["updated_at"] = datetime.now(timezone.utc)
    updates["version"] = listing["version"] + 1

    await doc_ref.update(updates)
    updated = await doc_ref.get()
    return _to_listing_response(updated.id, updated.to_dict())


async def cancel_listing(
    db: AsyncClient, listing_id: str, owner_uid: str
) -> ListingResponse:
    doc_ref = db.collection("listings").document(listing_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise NotFoundError(f"Listing {listing_id} not found")

    listing = doc.to_dict()
    if listing["owner_uid"] != owner_uid:
        raise ForbiddenError("You can only cancel your own listings")

    assert_transition(listing["listing_type"], listing["status"], "CANCELLED")

    now = datetime.now(timezone.utc)
    await doc_ref.update({
        "status": "CANCELLED",
        "updated_at": now,
        "version": listing["version"] + 1,
    })

    # Cancel any active matches for this listing
    matches_query = (
        db.collection("matches")
        .where("listing_id", "==", listing_id)
        .where("status", "in", ["PROPOSED", "ACCEPTED"])
    )
    async for match_doc in matches_query.stream():
        await db.collection("matches").document(match_doc.id).update({
            "status": MatchStatus.CANCELLED.value,
            "updated_at": now,
        })

    updated = await doc_ref.get()
    return _to_listing_response(updated.id, updated.to_dict())


async def claim_listing(
    db: AsyncClient,
    listing_id: str,
    claimant_uid: str,
    message: str | None = None,
) -> dict:
    """Atomically claim a lease transfer listing using a Firestore transaction."""
    transaction = db.transaction()
    return await _claim_listing_txn(transaction, db, listing_id, claimant_uid, message)


@async_transactional
async def _claim_listing_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    listing_id: str,
    claimant_uid: str,
    message: str | None,
) -> dict:
    listing_ref = db.collection("listings").document(listing_id)
    listing_snap = await listing_ref.get(transaction=transaction)

    if not listing_snap.exists:
        raise NotFoundError(f"Listing {listing_id} not found")

    listing = listing_snap.to_dict()

    if listing["status"] != LeaseTransferStatus.OPEN.value:
        raise ConflictError(
            f"Listing is in state {listing['status']}, not OPEN"
        )

    if listing["owner_uid"] == claimant_uid:
        raise BadRequestError("Cannot claim your own listing")

    if listing["listing_type"] != ListingType.LEASE_TRANSFER.value:
        raise BadRequestError("Use swap claim for swap requests")

    settings = get_settings()
    now = datetime.now(timezone.utc)

    # Create match document
    match_ref = db.collection("matches").document()
    match_data = {
        "match_type": ListingType.LEASE_TRANSFER.value,
        "status": MatchStatus.PROPOSED.value,
        "listing_id": listing_id,
        "claimant_uid": claimant_uid,
        "claimant_listing_id": None,
        "offered_room_id": listing["room_id"],
        "offered_room_category": listing["room_category"],
        "offered_room_building": listing["room_building"],
        "proposed_at": now,
        "responded_at": None,
        "expires_at": now + timedelta(hours=settings.match_expiry_hours),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    transaction.create(match_ref, match_data)

    # Update listing status to MATCHED
    transaction.update(listing_ref, {
        "status": LeaseTransferStatus.MATCHED.value,
        "version": listing["version"] + 1,
        "updated_at": now,
    })

    match_data["id"] = match_ref.id
    return match_data


async def create_swap_request(
    db: AsyncClient, owner_uid: str, data: SwapRequestCreate
) -> ListingResponse:
    await _check_no_active_listing(db, owner_uid)

    room_doc = await db.collection("rooms").document(data.room_id).get()
    if not room_doc.exists:
        raise NotFoundError(f"Room {data.room_id} not found")
    room = room_doc.to_dict()

    if data.lease_end_date <= data.lease_start_date:
        raise BadRequestError("lease_end_date must be after lease_start_date")

    if not data.desired_categories:
        raise BadRequestError("Must specify at least one desired category")

    settings = get_settings()
    now = datetime.now(timezone.utc)
    doc_data = {
        "listing_type": ListingType.SWAP_REQUEST.value,
        "status": SwapRequestStatus.OPEN.value,
        "version": 1,
        "owner_uid": owner_uid,
        "room_id": data.room_id,
        "room_category": room["category"],
        "room_building": room["building"],
        "lease_start_date": datetime.combine(data.lease_start_date, datetime.min.time(), tzinfo=timezone.utc),
        "lease_end_date": datetime.combine(data.lease_end_date, datetime.min.time(), tzinfo=timezone.utc),
        "move_in_date": (
            datetime.combine(data.move_in_date, datetime.min.time(), tzinfo=timezone.utc)
            if data.move_in_date
            else None
        ),
        "description": data.description,
        "asking_price": None,
        "desired_categories": [c.value for c in data.desired_categories],
        "desired_buildings": data.desired_buildings or [],
        "desired_min_start": (
            datetime.combine(data.desired_min_start, datetime.min.time(), tzinfo=timezone.utc)
            if data.desired_min_start
            else None
        ),
        "desired_max_end": (
            datetime.combine(data.desired_max_end, datetime.min.time(), tzinfo=timezone.utc)
            if data.desired_max_end
            else None
        ),
        "replacement_match_id": None,
        "target_match_id": None,
        "expires_at": now + timedelta(days=settings.listing_expiry_days),
        "created_at": now,
        "updated_at": now,
    }

    _, doc_ref = await db.collection("listings").add(doc_data)
    return _to_listing_response(doc_ref.id, doc_data)


async def claim_swap(
    db: AsyncClient,
    listing_id: str,
    claimant_uid: str,
    claimant_listing_id: str,
) -> dict:
    """Atomically claim a swap listing. Both parties must have swap listings."""
    transaction = db.transaction()
    return await _claim_swap_txn(
        transaction, db, listing_id, claimant_uid, claimant_listing_id
    )


@async_transactional
async def _claim_swap_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    listing_id: str,
    claimant_uid: str,
    claimant_listing_id: str,
) -> dict:
    # Read both listings in the transaction
    listing_ref = db.collection("listings").document(listing_id)
    listing_snap = await listing_ref.get(transaction=transaction)
    if not listing_snap.exists:
        raise NotFoundError(f"Listing {listing_id} not found")

    claimant_listing_ref = db.collection("listings").document(claimant_listing_id)
    claimant_listing_snap = await claimant_listing_ref.get(transaction=transaction)
    if not claimant_listing_snap.exists:
        raise NotFoundError(f"Claimant listing {claimant_listing_id} not found")

    listing = listing_snap.to_dict()
    claimant_listing = claimant_listing_snap.to_dict()

    # Validate listing types
    if listing["listing_type"] != ListingType.SWAP_REQUEST.value:
        raise BadRequestError("Target listing is not a swap request")
    if claimant_listing["listing_type"] != ListingType.SWAP_REQUEST.value:
        raise BadRequestError("Your listing is not a swap request")

    # Validate ownership
    if listing["owner_uid"] == claimant_uid:
        raise BadRequestError("Cannot claim your own listing")
    if claimant_listing["owner_uid"] != claimant_uid:
        raise ForbiddenError("Claimant listing does not belong to you")

    # Validate statuses
    if listing["status"] not in (
        SwapRequestStatus.OPEN.value,
        SwapRequestStatus.PARTIAL_MATCH.value,
    ):
        raise ConflictError(f"Target listing is {listing['status']}, not available")
    if claimant_listing["status"] not in (
        SwapRequestStatus.OPEN.value,
        SwapRequestStatus.PARTIAL_MATCH.value,
    ):
        raise ConflictError(f"Your listing is {claimant_listing['status']}, not available")

    settings = get_settings()
    now = datetime.now(timezone.utc)

    # Determine if this is a direct swap (both sides resolved at once)
    # Direct swap: I want their room category AND they want mine
    my_cat = claimant_listing["room_category"]
    their_cat = listing["room_category"]
    i_want_theirs = their_cat in claimant_listing.get("desired_categories", [])
    they_want_mine = my_cat in listing.get("desired_categories", [])

    if not (i_want_theirs and they_want_mine):
        raise BadRequestError("Listings are not compatible for a swap")

    # Create match: claimant takes listing's room (replacement for listing owner)
    match1_ref = db.collection("matches").document()
    match1_data = {
        "match_type": "SWAP_LEG",
        "status": MatchStatus.PROPOSED.value,
        "listing_id": listing_id,
        "claimant_uid": claimant_uid,
        "claimant_listing_id": claimant_listing_id,
        "offered_room_id": listing["room_id"],
        "offered_room_category": listing["room_category"],
        "offered_room_building": listing["room_building"],
        "proposed_at": now,
        "responded_at": None,
        "expires_at": now + timedelta(hours=settings.match_expiry_hours),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    transaction.create(match1_ref, match1_data)

    # Create match: listing owner takes claimant's room (replacement for claimant)
    match2_ref = db.collection("matches").document()
    match2_data = {
        "match_type": "SWAP_LEG",
        "status": MatchStatus.PROPOSED.value,
        "listing_id": claimant_listing_id,
        "claimant_uid": listing["owner_uid"],
        "claimant_listing_id": listing_id,
        "offered_room_id": claimant_listing["room_id"],
        "offered_room_category": claimant_listing["room_category"],
        "offered_room_building": claimant_listing["room_building"],
        "proposed_at": now,
        "responded_at": None,
        "expires_at": now + timedelta(hours=settings.match_expiry_hours),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    transaction.create(match2_ref, match2_data)

    # Update both listings to FULLY_MATCHED (direct swap)
    new_listing_status = SwapRequestStatus.FULLY_MATCHED.value
    assert_transition(listing["listing_type"], listing["status"], new_listing_status)
    transaction.update(listing_ref, {
        "status": new_listing_status,
        "replacement_match_id": match1_ref.id,
        "target_match_id": match2_ref.id,
        "version": listing["version"] + 1,
        "updated_at": now,
    })

    new_claimant_status = SwapRequestStatus.FULLY_MATCHED.value
    assert_transition(claimant_listing["listing_type"], claimant_listing["status"], new_claimant_status)
    transaction.update(claimant_listing_ref, {
        "status": new_claimant_status,
        "replacement_match_id": match2_ref.id,
        "target_match_id": match1_ref.id,
        "version": claimant_listing["version"] + 1,
        "updated_at": now,
    })

    return {
        "match_1": {**match1_data, "id": match1_ref.id},
        "match_2": {**match2_data, "id": match2_ref.id},
        "listing_status": new_listing_status,
        "claimant_listing_status": new_claimant_status,
    }
