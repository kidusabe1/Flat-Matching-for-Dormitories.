"""Tests for security authorization — IDOR prevention and admin role checks.

Verifies that:
- Match endpoints only return data to involved parties
- Transaction endpoints only return data to involved parties
- Room management is restricted to admin users
"""

import pytest

from tests.conftest import (
    _make_doc_snapshot,
    make_listing_data,
    make_match_data,
    make_room_data,
    make_transaction_data,
)


# ── Match IDOR Prevention ──


class TestMatchIDOR:
    @pytest.mark.asyncio
    async def test_get_match_as_claimant(self, client, mock_db):
        """Claimant can view their own match."""
        match = make_match_data(claimant_uid="test-uid-123")
        mock_db.register_doc("matches", "m-1", match)
        mock_db.register_doc("listings", "listing-1", make_listing_data(owner_uid="owner-x"))

        resp = await client.get("/api/v1/matches/m-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "m-1"

    @pytest.mark.asyncio
    async def test_get_match_as_listing_owner(self, client, mock_db):
        """Listing owner can view matches on their listing."""
        match = make_match_data(claimant_uid="someone-else")
        mock_db.register_doc("matches", "m-2", match)
        mock_db.register_doc("listings", "listing-1", make_listing_data(owner_uid="test-uid-123"))

        resp = await client.get("/api/v1/matches/m-2")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_match_forbidden_unrelated_user(self, client, mock_db):
        """Unrelated user cannot view someone else's match."""
        match = make_match_data(claimant_uid="user-A")
        mock_db.register_doc("matches", "m-3", match)
        mock_db.register_doc("listings", "listing-1", make_listing_data(owner_uid="user-B"))

        resp = await client.get("/api/v1/matches/m-3")
        assert resp.status_code == 403
        assert "not a party" in resp.json()["detail"].lower()


# ── Transaction IDOR Prevention ──


class TestTransactionIDOR:
    @pytest.mark.asyncio
    async def test_get_transaction_as_from_uid(self, client, mock_db):
        """Sender (from_uid) can view their transaction."""
        tx = make_transaction_data(from_uid="test-uid-123", to_uid="other")
        mock_db.register_doc("transactions", "tx-1", tx)

        resp = await client.get("/api/v1/transactions/tx-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_transaction_as_to_uid(self, client, mock_db):
        """Receiver (to_uid) can view their transaction."""
        tx = make_transaction_data(from_uid="other", to_uid="test-uid-123")
        mock_db.register_doc("transactions", "tx-2", tx)

        resp = await client.get("/api/v1/transactions/tx-2")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_transaction_as_party_a(self, client, mock_db):
        """Swap party A can view their transaction."""
        tx = make_transaction_data(
            transaction_type="SWAP",
            from_uid=None,
            to_uid=None,
            party_a_uid="test-uid-123",
            party_b_uid="other",
        )
        mock_db.register_doc("transactions", "tx-3", tx)

        resp = await client.get("/api/v1/transactions/tx-3")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_transaction_forbidden_unrelated_user(self, client, mock_db):
        """Unrelated user cannot view someone else's transaction."""
        tx = make_transaction_data(from_uid="user-A", to_uid="user-B")
        mock_db.register_doc("transactions", "tx-4", tx)

        resp = await client.get("/api/v1/transactions/tx-4")
        assert resp.status_code == 403
        assert "not a party" in resp.json()["detail"].lower()


# ── Room Admin Authorization ──


class TestRoomAdminAuth:
    @pytest.mark.asyncio
    async def test_create_room_admin_allowed(self, client, mock_db):
        """Admin user can create rooms."""
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "admin"})

        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
            "floor": 1,
            "room_number": "101",
            "category": "PARK_SHARED_2BR",
        })
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_room_student_forbidden(self, client, mock_db):
        """Non-admin user cannot create rooms."""
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "student"})

        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
            "floor": 1,
            "room_number": "101",
            "category": "PARK_SHARED_2BR",
        })
        assert resp.status_code == 403
        assert "administrator" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_room_no_role_forbidden(self, client, mock_db):
        """User with no role field cannot create rooms."""
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123"})

        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
            "floor": 1,
            "room_number": "101",
            "category": "PARK_SHARED_2BR",
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_room_no_profile_forbidden(self, client, mock_db):
        """User with no profile cannot create rooms."""
        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
            "floor": 1,
            "room_number": "101",
            "category": "PARK_SHARED_2BR",
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_room_admin_allowed(self, client, mock_db):
        """Admin user can update rooms."""
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "admin"})
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.put("/api/v1/rooms/room-1", json={
            "description": "Updated by admin",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_room_student_forbidden(self, client, mock_db):
        """Non-admin user cannot update rooms."""
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "student"})
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.put("/api/v1/rooms/room-1", json={
            "description": "Should fail",
        })
        assert resp.status_code == 403
