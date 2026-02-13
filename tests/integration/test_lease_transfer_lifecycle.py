"""Integration test: Full lease transfer lifecycle through HTTP routes."""

import pytest

from tests.conftest import (
    _make_doc_snapshot,
    make_listing_data,
    make_match_data,
    make_room_data,
    make_transaction_data,
)


class TestLeaseTransferLifecycle:
    """End-to-end lifecycle: create listing → claim → accept → confirm."""

    @pytest.mark.asyncio
    async def test_rebid_after_cancel(self, client, mock_db):
        """Regression: User B cancels bid, then re-bids → should succeed (not 409)."""
        listing = make_listing_data(
            owner_uid="owner-user",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-rebid", listing)
        
        # Existing CANCELLED bid
        bid_id = "listing-rebid_test-uid-123" # Deterministic ID: listing_id + claimant_uid
        cancelled_bid = make_match_data(
            status="CANCELLED",
            listing_id="listing-rebid",
            claimant_uid="test-uid-123",
        )
        mock_db.register_doc("matches", bid_id, cancelled_bid)

        # Act: Re-claim
        resp = await client.post("/api/v1/listings/listing-rebid/claim", json={
            "message": "I want this room again!",
        })
        
        # Assert: Should be 200 OK, not 409 Conflict
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PROPOSED"


    @pytest.mark.asyncio
    async def test_create_listing_returns_open(self, client, mock_db):
        """Step 1: User A creates a lease transfer listing → OPEN."""
        mock_db.register_doc("rooms", "room-1", make_room_data(occupant_uid="test-uid-123"))
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/lease-transfer", json={
            "room_id": "room-1",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
            "description": "Full lifecycle test",
            "asking_price": 1500,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "OPEN"
        assert data["listing_type"] == "LEASE_TRANSFER"
        assert data["asking_price"] == 1500

    @pytest.mark.asyncio
    async def test_claim_listing_creates_bid(self, client, mock_db):
        """Step 2: User B (test user) claims User A's listing → match PROPOSED."""
        listing = make_listing_data(
            owner_uid="owner-user",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.post("/api/v1/listings/listing-1/claim", json={
            "message": "I want this room!",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_listing_bids(self, client, mock_db):
        """Step 3: Listing owner views bids on their listing."""
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        bids = [
            _make_doc_snapshot("bid-1", make_match_data(
                status="PROPOSED", listing_id="listing-1", claimant_uid="user-B",
            )),
        ]
        mock_db.register_collection_docs("matches", bids)

        resp = await client.get("/api/v1/listings/listing-1/bids")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_accept_bid_creates_transaction(self, client, mock_db):
        """Step 4: Owner accepts a bid → listing → PENDING_APPROVAL, transaction created."""
        listing = make_listing_data(
            owner_uid="test-uid-123", status="OPEN", version=1,
        )
        mock_db.register_doc("listings", "listing-1", listing)

        match = make_match_data(
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="user-B",
        )
        mock_db.register_doc("matches", "match-1", match)

        # Other bids to cancel
        mock_db.register_collection_docs("matches", [])

        resp = await client.post("/api/v1/matches/match-1/accept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ACCEPTED"

    @pytest.mark.asyncio
    async def test_confirm_transaction_completes(self, client, mock_db):
        """Step 5: Owner confirms transaction → COMPLETED, room occupant updated."""
        tx = make_transaction_data(
            transaction_type="LEASE_TRANSFER",
            status="PENDING",
            from_uid="test-uid-123",
            to_uid="user-B",
            room_id="room-1",
        )
        mock_db.register_doc("transactions", "tx-1", tx)
        mock_db.register_doc("rooms", "room-1", make_room_data(occupant_uid="test-uid-123"))
        mock_db.register_doc("matches", "match-1", make_match_data(
            status="ACCEPTED", listing_id="listing-1",
        ))
        mock_db.register_doc("listings", "listing-1", make_listing_data(
            status="PENDING_APPROVAL",
        ))
        mock_db.register_collection_docs("transactions", [])

        resp = await client.post("/api/v1/transactions/tx-1/confirm")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
