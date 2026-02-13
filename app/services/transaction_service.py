from datetime import datetime, date, timezone

from google.cloud.firestore_v1 import AsyncClient, async_transactional, AsyncTransaction

from app.middleware.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.enums import (
    LeaseTransferStatus,
    MatchStatus,
    SwapRequestStatus,
    TransactionStatus,
)
from app.models.transaction import TransactionResponse


def _to_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    return val


def _to_transaction_response(doc_id: str, data: dict) -> TransactionResponse:
    return TransactionResponse(
        id=doc_id,
        transaction_type=data["transaction_type"],
        status=data["status"],
        match_id=data.get("match_id"),
        match_ids=data.get("match_ids"),
        from_uid=data.get("from_uid"),
        to_uid=data.get("to_uid"),
        room_id=data.get("room_id"),
        party_a_uid=data.get("party_a_uid"),
        party_a_room_id=data.get("party_a_room_id"),
        party_b_uid=data.get("party_b_uid"),
        party_b_room_id=data.get("party_b_room_id"),
        lease_start_date=_to_date(data.get("lease_start_date")),
        lease_end_date=_to_date(data.get("lease_end_date")),
        initiated_at=data.get("initiated_at"),
        completed_at=data.get("completed_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


async def get_transaction(db: AsyncClient, tx_id: str, requester_uid: str) -> TransactionResponse:
    doc = await db.collection("transactions").document(tx_id).get()
    if not doc.exists:
        raise NotFoundError(f"Transaction {tx_id} not found")
    data = doc.to_dict()

    # Verify the requester is a party to this transaction
    involved = [
        data.get("from_uid"),
        data.get("to_uid"),
        data.get("party_a_uid"),
        data.get("party_b_uid"),
    ]
    if requester_uid not in [u for u in involved if u]:
        raise ForbiddenError("You are not a party in this transaction")

    return _to_transaction_response(doc.id, data)


async def get_user_transactions(
    db: AsyncClient, uid: str, status: str | None = None
) -> list[TransactionResponse]:
    results = []

    # Check as from_uid (lease transfer sender)
    query = db.collection("transactions").where("from_uid", "==", uid)
    if status:
        query = query.where("status", "==", status)
    async for doc in query.stream():
        results.append(_to_transaction_response(doc.id, doc.to_dict()))

    # Check as to_uid (lease transfer receiver)
    query = db.collection("transactions").where("to_uid", "==", uid)
    if status:
        query = query.where("status", "==", status)
    async for doc in query.stream():
        tx = _to_transaction_response(doc.id, doc.to_dict())
        if not any(r.id == tx.id for r in results):
            results.append(tx)

    # Check as party_a (swap)
    query = db.collection("transactions").where("party_a_uid", "==", uid)
    if status:
        query = query.where("status", "==", status)
    async for doc in query.stream():
        tx = _to_transaction_response(doc.id, doc.to_dict())
        if not any(r.id == tx.id for r in results):
            results.append(tx)

    # Check as party_b (swap)
    query = db.collection("transactions").where("party_b_uid", "==", uid)
    if status:
        query = query.where("status", "==", status)
    async for doc in query.stream():
        tx = _to_transaction_response(doc.id, doc.to_dict())
        if not any(r.id == tx.id for r in results):
            results.append(tx)

    return results


async def confirm_transaction(
    db: AsyncClient, tx_id: str, uid: str
) -> TransactionResponse:
    """Confirm a lease transfer transaction — atomically update room occupancy."""
    transaction = db.transaction()
    return await _confirm_lease_transfer_txn(transaction, db, tx_id, uid)


@async_transactional
async def _confirm_lease_transfer_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    tx_id: str,
    uid: str,
) -> TransactionResponse:
    tx_ref = db.collection("transactions").document(tx_id)
    tx_snap = await tx_ref.get(transaction=transaction)
    if not tx_snap.exists:
        raise NotFoundError(f"Transaction {tx_id} not found")

    tx_data = tx_snap.to_dict()
    if tx_data["status"] != TransactionStatus.PENDING.value:
        raise ConflictError(f"Transaction is {tx_data['status']}, not PENDING")

    # Only involved parties can confirm
    involved = [
        tx_data.get("from_uid"),
        tx_data.get("to_uid"),
        tx_data.get("party_a_uid"),
        tx_data.get("party_b_uid"),
    ]
    if uid not in [u for u in involved if u]:
        raise ForbiddenError("You are not a party in this transaction")

    now = datetime.now(timezone.utc)

    if tx_data["transaction_type"] == "LEASE_TRANSFER":
        # --- All reads first ---
        room_ref = db.collection("rooms").document(tx_data["room_id"])
        room_snap = await room_ref.get(transaction=transaction)
        if not room_snap.exists:
            raise NotFoundError("Room not found")

        room = room_snap.to_dict()
        if room.get("occupant_uid") and room["occupant_uid"] != tx_data["from_uid"]:
            raise ConflictError("Room occupant has changed — cannot complete transfer")

        match_ref = db.collection("matches").document(tx_data["match_id"])
        match_snap = await match_ref.get(transaction=transaction)

        listing_ref = None
        if match_snap.exists:
            match_d = match_snap.to_dict()
            listing_ref = db.collection("listings").document(match_d["listing_id"])

        # --- All writes after reads ---
        transaction.update(room_ref, {
            "occupant_uid": tx_data["to_uid"],
            "updated_at": now,
        })

        from_user_ref = db.collection("users").document(tx_data["from_uid"])
        transaction.update(from_user_ref, {
            "current_room_id": None,
            "updated_at": now,
        })

        to_user_ref = db.collection("users").document(tx_data["to_uid"])
        transaction.update(to_user_ref, {
            "current_room_id": tx_data["room_id"],
            "updated_at": now,
        })

        if match_snap.exists:
            transaction.update(match_ref, {
                "status": MatchStatus.ACCEPTED.value,
                "updated_at": now,
            })
            if listing_ref:
                transaction.update(listing_ref, {
                    "status": LeaseTransferStatus.COMPLETED.value,
                    "updated_at": now,
                })

        # Cancel other PENDING transactions for the same room
        other_txns_query = (
            db.collection("transactions")
            .where("room_id", "==", tx_data["room_id"])
            .where("status", "==", TransactionStatus.PENDING.value)
        )
        async for other_doc in other_txns_query.stream():
            if other_doc.id != tx_id:
                transaction.update(
                    db.collection("transactions").document(other_doc.id),
                    {"status": TransactionStatus.CANCELLED.value, "updated_at": now},
                )

    elif tx_data["transaction_type"] == "SWAP":
        # --- All reads first ---
        room_a_ref = db.collection("rooms").document(tx_data["party_a_room_id"])
        room_b_ref = db.collection("rooms").document(tx_data["party_b_room_id"])
        room_a_snap = await room_a_ref.get(transaction=transaction)
        room_b_snap = await room_b_ref.get(transaction=transaction)

        if not room_a_snap.exists or not room_b_snap.exists:
            raise NotFoundError("One of the rooms not found")

        room_a = room_a_snap.to_dict()
        room_b = room_b_snap.to_dict()

        if room_a.get("occupant_uid") and room_a["occupant_uid"] != tx_data["party_a_uid"]:
            raise ConflictError("Room A occupant has changed")
        if room_b.get("occupant_uid") and room_b["occupant_uid"] != tx_data["party_b_uid"]:
            raise ConflictError("Room B occupant has changed")

        # Read all matches and their listings before any writes
        match_listing_pairs = []
        for mid in (tx_data.get("match_ids") or []):
            m_ref = db.collection("matches").document(mid)
            m_snap = await m_ref.get(transaction=transaction)
            if m_snap.exists:
                m_data = m_snap.to_dict()
                l_ref = db.collection("listings").document(m_data["listing_id"])
                match_listing_pairs.append((m_ref, l_ref))

        # --- All writes after reads ---
        transaction.update(room_a_ref, {
            "occupant_uid": tx_data["party_b_uid"],
            "updated_at": now,
        })
        transaction.update(room_b_ref, {
            "occupant_uid": tx_data["party_a_uid"],
            "updated_at": now,
        })

        user_a_ref = db.collection("users").document(tx_data["party_a_uid"])
        user_b_ref = db.collection("users").document(tx_data["party_b_uid"])
        transaction.update(user_a_ref, {
            "current_room_id": tx_data["party_b_room_id"],
            "updated_at": now,
        })
        transaction.update(user_b_ref, {
            "current_room_id": tx_data["party_a_room_id"],
            "updated_at": now,
        })

        for m_ref, l_ref in match_listing_pairs:
            transaction.update(m_ref, {
                "status": MatchStatus.ACCEPTED.value,
                "updated_at": now,
            })
            transaction.update(l_ref, {
                "status": SwapRequestStatus.COMPLETED.value,
                "updated_at": now,
            })

    # Mark transaction completed
    transaction.update(tx_ref, {
        "status": TransactionStatus.COMPLETED.value,
        "completed_at": now,
        "updated_at": now,
    })

    tx_data["status"] = TransactionStatus.COMPLETED.value
    tx_data["completed_at"] = now
    return _to_transaction_response(tx_snap.id, tx_data)


async def cancel_transaction(
    db: AsyncClient, tx_id: str, uid: str
) -> TransactionResponse:
    """Cancel a pending transaction and reopen the listing."""
    transaction = db.transaction()
    return await _cancel_transaction_txn(transaction, db, tx_id, uid)


@async_transactional
async def _cancel_transaction_txn(
    transaction: AsyncTransaction,
    db: AsyncClient,
    tx_id: str,
    uid: str,
) -> TransactionResponse:
    tx_ref = db.collection("transactions").document(tx_id)
    tx_snap = await tx_ref.get(transaction=transaction)
    if not tx_snap.exists:
        raise NotFoundError(f"Transaction {tx_id} not found")

    tx_data = tx_snap.to_dict()
    if tx_data["status"] != TransactionStatus.PENDING.value:
        raise ConflictError(f"Transaction is {tx_data['status']}, not PENDING")

    involved = [
        tx_data.get("from_uid"),
        tx_data.get("to_uid"),
        tx_data.get("party_a_uid"),
        tx_data.get("party_b_uid"),
    ]
    if uid not in [u for u in involved if u]:
        raise ForbiddenError("You are not a party in this transaction")

    now = datetime.now(timezone.utc)

    # --- All reads first ---
    match_ref = None
    listing_ref = None
    if tx_data.get("match_id"):
        match_ref = db.collection("matches").document(tx_data["match_id"])
        match_snap = await match_ref.get(transaction=transaction)
        if match_snap.exists:
            match_d = match_snap.to_dict()
            listing_ref = db.collection("listings").document(match_d["listing_id"])

    # --- All writes after reads ---
    transaction.update(tx_ref, {
        "status": TransactionStatus.CANCELLED.value,
        "updated_at": now,
    })

    if match_ref and match_snap.exists:
        transaction.update(match_ref, {
            "status": MatchStatus.CANCELLED.value,
            "updated_at": now,
        })
        if listing_ref:
            transaction.update(listing_ref, {
                "status": "OPEN",
                "updated_at": now,
            })

    tx_data["status"] = TransactionStatus.CANCELLED.value
    return _to_transaction_response(tx_snap.id, tx_data)
