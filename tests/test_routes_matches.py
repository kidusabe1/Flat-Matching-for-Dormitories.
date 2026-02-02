"""Tests for match API routes."""

import pytest

from tests.conftest import _make_doc_snapshot, make_listing_data, make_match_data


class TestGetMyMatches:
    @pytest.mark.asyncio
    async def test_get_my_matches_as_claimant(self, client, mock_db):
        match = make_match_data(claimant_uid="test-uid-123")
        match_snap = _make_doc_snapshot("match-1", match)
        mock_db.register_collection_docs("matches", [match_snap])
        # Also need listing query for owner-side matches
        mock_db.register_collection_docs("listings", [])

        resp = await client.get("/api/v1/matches/my")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_my_matches_with_status_filter(self, client, mock_db):
        mock_db.register_collection_docs("matches", [])
        mock_db.register_collection_docs("listings", [])

        resp = await client.get("/api/v1/matches/my?status=PROPOSED")
        assert resp.status_code == 200


class TestGetMatch:
    @pytest.mark.asyncio
    async def test_get_match(self, client, mock_db):
        match = make_match_data()
        mock_db.register_doc("matches", "match-1", match)

        resp = await client.get("/api/v1/matches/match-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "match-1"
        assert data["status"] == "PROPOSED"

    @pytest.mark.asyncio
    async def test_get_match_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/matches/nonexistent")
        assert resp.status_code == 404
