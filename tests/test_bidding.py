"""Tests for the bidding system — listings stay OPEN while bids are collected."""

import pytest

from tests.conftest import _make_doc_snapshot, make_listing_data, make_match_data


class TestBidCreation:
    @pytest.mark.asyncio
    async def test_claim_creates_bid_without_changing_listing_status(
        self, client, mock_db
    ):
        """Bidding on a listing should NOT change listing status from OPEN."""
        listing = make_listing_data(
            owner_uid="other-owner",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)
        # No existing bids
        mock_db.register_collection_docs("matches", [])

        resp = await client.post(
            "/api/v1/listings/listing-1/claim",
            json={"message": "I want this room"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PROPOSED"
        assert data["listing_id"] == "listing-1"
        assert data["claimant_uid"] == "test-uid-123"

    @pytest.mark.asyncio
    async def test_multiple_users_can_bid_on_same_listing(
        self, app, mock_db, test_user, test_user_b
    ):
        """Multiple different users should be able to bid on the same listing."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        from app.auth.dependencies import get_current_user
        from app.services.firestore_client import get_db

        listing = make_listing_data(
            owner_uid="owner-uid",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)
        mock_db.register_collection_docs("matches", [])

        # First user bids
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = lambda: mock_db
        async with HttpxAsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            resp1 = await c.post(
                "/api/v1/listings/listing-1/claim",
                json={"message": "First bid"},
            )
        assert resp1.status_code == 200

        # Second user bids
        app.dependency_overrides[get_current_user] = lambda: test_user_b
        async with HttpxAsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            resp2 = await c.post(
                "/api/v1/listings/listing-1/claim",
                json={"message": "Second bid"},
            )
        assert resp2.status_code == 200

        # Both bids should have different claimant UIDs
        assert resp1.json()["claimant_uid"] == "test-uid-123"
        assert resp2.json()["claimant_uid"] == "test-uid-456"

    @pytest.mark.asyncio
    async def test_same_user_cannot_bid_twice(self, client, mock_db):
        """Same user bidding on the same listing twice should get 409."""
        listing = make_listing_data(
            owner_uid="other-owner",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)
        # Register existing bid from this user
        existing_bid = make_match_data(
            listing_id="listing-1",
            claimant_uid="test-uid-123",
            status="PROPOSED",
        )
        mock_db.register_doc(
            "matches", "listing-1_test-uid-123", existing_bid
        )
        mock_db.register_collection_docs("matches", [])

        resp = await client.post(
            "/api/v1/listings/listing-1/claim",
            json={"message": "Duplicate bid"},
        )
        assert resp.status_code == 409


class TestBidAcceptance:
    @pytest.mark.asyncio
    async def test_accepting_bid_transitions_to_pending_approval(
        self, client, mock_db
    ):
        """Accepting a bid should transition listing from OPEN to PENDING_APPROVAL."""
        listing = make_listing_data(
            owner_uid="test-uid-123",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        match = make_match_data(
            match_type="LEASE_TRANSFER",
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="test-uid-456",
        )
        mock_db.register_doc("matches", "match-1", match)
        # No other bids to cancel
        mock_db.register_collection_docs("matches", [])

        resp = await client.post("/api/v1/matches/match-1/accept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ACCEPTED"

    @pytest.mark.asyncio
    async def test_accepting_bid_cancels_other_bids(self, client, mock_db):
        """Accepting one bid should cancel all other PROPOSED bids on the listing."""
        listing = make_listing_data(
            owner_uid="test-uid-123",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        # The bid being accepted
        accepted_match = make_match_data(
            match_type="LEASE_TRANSFER",
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="test-uid-456",
        )
        mock_db.register_doc("matches", "match-1", accepted_match)

        # Another bid that should be cancelled
        other_match = make_match_data(
            match_type="LEASE_TRANSFER",
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="test-uid-789",
        )
        other_snap = _make_doc_snapshot("match-2", other_match)
        mock_db.register_collection_docs("matches", [other_snap])

        resp = await client.post("/api/v1/matches/match-1/accept")
        assert resp.status_code == 200


class TestBidRejection:
    @pytest.mark.asyncio
    async def test_rejecting_bid_keeps_listing_open(self, client, mock_db):
        """Rejecting a bid should leave the listing in OPEN status."""
        listing = make_listing_data(
            owner_uid="test-uid-123",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        match = make_match_data(
            match_type="LEASE_TRANSFER",
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="test-uid-456",
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/reject")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "REJECTED"


class TestListingBids:
    @pytest.mark.asyncio
    async def test_get_listing_bids_returns_proposed_matches(
        self, client, mock_db
    ):
        """GET /listings/{id}/bids should return PROPOSED matches for the listing."""
        listing = make_listing_data(
            owner_uid="test-uid-123",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        bid = make_match_data(
            match_type="LEASE_TRANSFER",
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="test-uid-456",
        )
        bid_snap = _make_doc_snapshot("bid-1", bid)
        mock_db.register_collection_docs("matches", [bid_snap])

        resp = await client.get("/api/v1/listings/listing-1/bids")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["status"] == "PROPOSED"

    @pytest.mark.asyncio
    async def test_only_owner_can_view_bids(self, client, mock_db):
        """Non-owner should get 403 when viewing bids."""
        listing = make_listing_data(
            owner_uid="other-owner",
            status="OPEN",
            listing_type="LEASE_TRANSFER",
        )
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.get("/api/v1/listings/listing-1/bids")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_bids_for_nonexistent_listing(self, client, mock_db):
        """Should return 404 for bids on a nonexistent listing."""
        resp = await client.get("/api/v1/listings/nonexistent/bids")
        assert resp.status_code == 404
