"""Tests for room API routes — CRUD operations."""

import pytest

from tests.conftest import _make_doc_snapshot, make_room_data


class TestCreateRoom:
    @pytest.mark.asyncio
    async def test_create_room(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "admin"})

        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 3",
            "floor": 2,
            "room_number": "204",
            "category": "PARK_SHARED_2BR",
            "description": "Corner room",
            "amenities": ["AC", "balcony"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["building"] == "Building 3"
        assert data["category"] == "PARK_SHARED_2BR"
        assert data["floor"] == 2
        assert data["room_number"] == "204"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_room_forbidden_non_admin(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "student"})

        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 3",
            "floor": 2,
            "room_number": "204",
            "category": "PARK_SHARED_2BR",
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_room_invalid_category(self, client, mock_db):
        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
            "floor": 1,
            "room_number": "101",
            "category": "NONEXISTENT_CATEGORY",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_room_missing_required(self, client, mock_db):
        resp = await client.post("/api/v1/rooms", json={
            "building": "Building 1",
        })
        assert resp.status_code == 422


class TestGetRoom:
    @pytest.mark.asyncio
    async def test_get_room(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.get("/api/v1/rooms/room-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "room-1"
        assert data["category"] == "PARK_SHARED_2BR"

    @pytest.mark.asyncio
    async def test_get_room_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/rooms/nonexistent")
        assert resp.status_code == 404


class TestListRooms:
    @pytest.mark.asyncio
    async def test_list_rooms(self, client, mock_db):
        rooms = [
            _make_doc_snapshot(f"room-{i}", make_room_data())
            for i in range(3)
        ]
        mock_db.register_collection_docs("rooms", rooms)

        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_rooms_with_filters(self, client, mock_db):
        mock_db.register_collection_docs("rooms", [])

        resp = await client.get("/api/v1/rooms?category=PARK_SHARED_2BR&building=Building+3")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_rooms_empty(self, client, mock_db):
        mock_db.register_collection_docs("rooms", [])

        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        assert resp.json() == []


class TestUpdateRoom:
    @pytest.mark.asyncio
    async def test_update_room(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "admin"})
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.put("/api/v1/rooms/room-1", json={
            "description": "Updated description",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_room_not_found(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "admin"})

        resp = await client.put("/api/v1/rooms/nonexistent", json={
            "description": "Updated",
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_room_forbidden_non_admin(self, client, mock_db):
        mock_db.register_doc("users", "test-uid-123", {"uid": "test-uid-123", "role": "student"})
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.put("/api/v1/rooms/room-1", json={
            "description": "Updated",
        })
        assert resp.status_code == 403
