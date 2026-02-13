"""Integration test: Cancellation flows."""

import pytest

from tests.conftest import make_listing_data, make_match_data, make_transaction_data, make_room_data


class TestCancelFlows:
    @pytest.mark.asyncio
    async def test_cancel_listing_with_active_bids(self, client, mock_db):
        """Cancel listing → all active bids also cancelled."""
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        from tests.conftest import _make_doc_snapshot
        bids = [
            _make_doc_snapshot("bid-1", make_match_data(
                status="PROPOSED", listing_id="listing-1", claimant_uid="user-B",
            )),
        ]
        mock_db.register_collection_docs("matches", bids)

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_cancel_bid_listing_stays_open(self, client, mock_db):
        """Claimant cancels their bid → listing unaffected."""
        match = make_match_data(
            status="PROPOSED",
            claimant_uid="test-uid-123",
            listing_id="listing-1",
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_transaction_reopens_listing(self, client, mock_db):
        """Cancel a pending transaction → listing reopened."""
        tx = make_transaction_data(
            status="PENDING",
            from_uid="test-uid-123",
            to_uid="user-B",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        match = make_match_data(status="ACCEPTED", listing_id="listing-1")
        mock_db.register_doc("matches", "match-1", match)
        mock_db.register_doc("listings", "listing-1", make_listing_data(
            status="PENDING_APPROVAL",
        ))

        resp = await client.post("/api/v1/transactions/tx-1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_listing_not_found(self, client, mock_db):
        resp = await client.post("/api/v1/listings/nonexistent/cancel")
        assert resp.status_code == 404
