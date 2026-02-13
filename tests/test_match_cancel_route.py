"""Tests for match cancel route — POST /matches/{id}/cancel."""

import pytest

from tests.conftest import make_match_data


class TestCancelMatch:
    @pytest.mark.asyncio
    async def test_cancel_own_bid(self, client, mock_db):
        """Claimant can cancel their own PROPOSED bid."""
        match = make_match_data(
            status="PROPOSED",
            claimant_uid="test-uid-123",
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_bid_not_claimant_forbidden(self, client, mock_db):
        """Non-claimant cannot cancel someone else's bid."""
        match = make_match_data(
            status="PROPOSED",
            claimant_uid="other-user",  # Not test-uid-123
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/cancel")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_already_accepted_fails(self, client, mock_db):
        """Cannot cancel an already ACCEPTED match."""
        match = make_match_data(
            status="ACCEPTED",
            claimant_uid="test-uid-123",
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/cancel")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_match(self, client, mock_db):
        resp = await client.post("/api/v1/matches/nonexistent/cancel")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_rejected_match_fails(self, client, mock_db):
        """Cannot cancel an already REJECTED match."""
        match = make_match_data(
            status="REJECTED",
            claimant_uid="test-uid-123",
        )
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.post("/api/v1/matches/match-1/cancel")
        assert resp.status_code == 409
