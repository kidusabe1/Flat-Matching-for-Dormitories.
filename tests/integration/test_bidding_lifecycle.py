"""Integration test: Multi-bidder lifecycle."""

import pytest

from tests.conftest import (
    _make_doc_snapshot,
    make_listing_data,
    make_match_data,
)


class TestBiddingLifecycle:
    """Multiple users bid on a listing → owner rejects some, accepts one."""

    @pytest.mark.asyncio
    async def test_reject_bid_keeps_listing_open(self, client, mock_db):
        """Owner rejects a bid → match REJECTED, listing stays OPEN."""
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        match = make_match_data(
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="user-B",
        )
        mock_db.register_doc("matches", "match-B", match)

        resp = await client.post("/api/v1/matches/match-B/reject")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_accept_bid_after_rejection(self, client, mock_db):
        """Owner accepts a different bid after rejecting the first."""
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        match_c = make_match_data(
            status="PROPOSED",
            listing_id="listing-1",
            claimant_uid="user-C",
        )
        mock_db.register_doc("matches", "match-C", match_c)

        # No other pending bids
        mock_db.register_collection_docs("matches", [])

        resp = await client.post("/api/v1/matches/match-C/accept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ACCEPTED"

    @pytest.mark.asyncio
    async def test_view_bids_shows_correct_list(self, client, mock_db):
        """Owner can view all PROPOSED bids on their listing."""
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        bids = [
            _make_doc_snapshot("bid-B", make_match_data(
                status="PROPOSED", listing_id="listing-1", claimant_uid="user-B",
            )),
            _make_doc_snapshot("bid-C", make_match_data(
                status="PROPOSED", listing_id="listing-1", claimant_uid="user-C",
            )),
        ]
        mock_db.register_collection_docs("matches", bids)

        resp = await client.get("/api/v1/listings/listing-1/bids")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
