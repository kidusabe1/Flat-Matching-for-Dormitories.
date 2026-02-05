"""Tests for match contact endpoint and profile update with room."""

import pytest

from tests.conftest import make_listing_data, make_match_data


class TestMatchContact:
    """Tests for GET /api/v1/matches/{match_id}/contact."""

    def _setup_accepted_match(self, mock_db, requester_is_owner=True):
        """Helper to set up an accepted match with associated listing and users."""
        listing_data = make_listing_data(
            owner_uid="test-uid-123",
            room_id="room-1",
        )
        match_data = make_match_data(
            match_type="LEASE_TRANSFER",
            status="ACCEPTED",
            listing_id="listing-1",
            claimant_uid="test-uid-456",
        )

        mock_db.register_doc("matches", "match-1", match_data)
        mock_db.register_doc("listings", "listing-1", listing_data)
        mock_db.register_doc("users", "test-uid-456", {
            "uid": "test-uid-456",
            "full_name": "Other Student",
            "phone": "+972501234568",
            "email": "other@biu.ac.il",
            "student_id": "211234568",
        })
        mock_db.register_doc("users", "test-uid-123", {
            "uid": "test-uid-123",
            "full_name": "Test Student",
            "phone": "+972501234567",
            "email": "test@biu.ac.il",
            "student_id": "211234567",
        })

    @pytest.mark.asyncio
    async def test_get_contact_as_listing_owner(self, client, mock_db):
        self._setup_accepted_match(mock_db)

        resp = await client.get("/api/v1/matches/match-1/contact")
        assert resp.status_code == 200
        data = resp.json()
        # test_user (uid-123) is the listing owner, so they get claimant's info
        assert data["name"] == "Other Student"
        assert data["phone"] == "+972501234568"

    @pytest.mark.asyncio
    async def test_get_contact_as_claimant(self, client, mock_db, app, test_user_b):
        """When the claimant requests contact, they get the listing owner's info."""
        self._setup_accepted_match(mock_db)
        # Override auth to be the claimant
        from app.auth.dependencies import get_current_user
        app.dependency_overrides[get_current_user] = lambda: test_user_b

        resp = await client.get("/api/v1/matches/match-1/contact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Student"
        assert data["phone"] == "+972501234567"

    @pytest.mark.asyncio
    async def test_contact_not_accepted_match(self, client, mock_db):
        match_data = make_match_data(status="PROPOSED", listing_id="listing-1")
        mock_db.register_doc("matches", "match-1", match_data)

        resp = await client.get("/api/v1/matches/match-1/contact")
        assert resp.status_code == 409
        assert "accepted" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_contact_match_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/matches/nonexistent/contact")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_contact_not_a_party(self, client, mock_db):
        """User who is neither owner nor claimant gets forbidden."""
        listing_data = make_listing_data(owner_uid="someone-else")
        match_data = make_match_data(
            status="ACCEPTED",
            listing_id="listing-1",
            claimant_uid="another-person",
        )
        mock_db.register_doc("matches", "match-1", match_data)
        mock_db.register_doc("listings", "listing-1", listing_data)

        resp = await client.get("/api/v1/matches/match-1/contact")
        assert resp.status_code == 403


class TestProfileUpdateWithRoom:
    """Tests for PUT /api/v1/users/me with room changes."""

    @pytest.mark.asyncio
    async def test_update_phone(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {
            "uid": "test-uid-123",
            "email": "test@biu.ac.il",
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
            "current_room_id": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })

        resp = await client.put("/api/v1/users/me", json={
            "phone": "+972509999999",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_room_and_name(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {
            "uid": "test-uid-123",
            "email": "test@biu.ac.il",
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
            "current_room_id": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })

        resp = await client.put("/api/v1/users/me", json={
            "full_name": "New Name",
            "current_room_id": "room-42",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self, client, mock_db):
        resp = await client.put("/api/v1/users/me", json={
            "phone": "+972509999999",
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_profile_with_room(self, client, mock_db):
        resp = await client.post("/api/v1/users/profile", json={
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
            "current_room_id": "room-1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["current_room_id"] == "room-1"
