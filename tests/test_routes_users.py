"""Tests for user API routes."""

import pytest


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestUserRoutes:
    @pytest.mark.asyncio
    async def test_create_profile(self, client, mock_db):
        resp = await client.post("/api/v1/users/profile", json={
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["uid"] == "test-uid-123"
        assert data["full_name"] == "Test Student"
        assert data["student_id"] == "211234567"

    @pytest.mark.asyncio
    async def test_get_my_profile(self, client, mock_db):
        profile_data = {
            "uid": "test-uid-123",
            "email": "test@biu.ac.il",
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
            "current_room_id": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        mock_db.register_doc("users", "test-uid-123", profile_data)

        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["uid"] == "test-uid-123"
        assert data["full_name"] == "Test Student"

    @pytest.mark.asyncio
    async def test_get_my_profile_not_found(self, client, mock_db):
        # No doc registered -> not found
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile(self, client, mock_db):
        profile_data = {
            "uid": "test-uid-123",
            "email": "test@biu.ac.il",
            "full_name": "Test Student",
            "student_id": "211234567",
            "phone": "+972501234567",
            "current_room_id": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        mock_db.register_doc("users", "test-uid-123", profile_data)

        resp = await client.put("/api/v1/users/me", json={
            "full_name": "Updated Name",
        })
        # The update will succeed since we mock the Firestore calls
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_public_profile(self, client, mock_db):
        profile_data = {
            "uid": "other-uid",
            "email": "other@biu.ac.il",
            "full_name": "Other Student",
            "student_id": "211234568",
            "phone": "+972501234568",
            "current_room_id": "room-1",
        }
        mock_db.register_doc("users", "other-uid", profile_data)

        resp = await client.get("/api/v1/users/other-uid")
        assert resp.status_code == 200
        data = resp.json()
        assert data["uid"] == "other-uid"
        assert data["full_name"] == "Other Student"
        # Public profile should not include phone/email/student_id
        assert "phone" not in data
        assert "email" not in data
        assert "student_id" not in data

    @pytest.mark.asyncio
    async def test_get_public_profile_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/users/nonexistent")
        assert resp.status_code == 404
