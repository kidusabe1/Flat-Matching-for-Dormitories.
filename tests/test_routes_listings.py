"""Tests for listing API routes."""

import pytest

from tests.conftest import _make_doc_snapshot, make_listing_data, make_room_data


class TestCreateLeaseTransfer:
    @pytest.mark.asyncio
    async def test_create_lease_transfer(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data())
        # No active listings for this user (empty stream)
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/lease-transfer", json={
            "room_id": "room-1",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
            "description": "Nice room for semester",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["listing_type"] == "LEASE_TRANSFER"
        assert data["status"] == "OPEN"
        assert data["room_category"] == "PARK_SHARED_2BR"

    @pytest.mark.asyncio
    async def test_invalid_dates_rejected(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data())
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/lease-transfer", json={
            "room_id": "room-1",
            "lease_start_date": "2026-08-31",
            "lease_end_date": "2026-03-01",
            "description": "Bad dates",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_room_not_found(self, client, mock_db):
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/lease-transfer", json={
            "room_id": "nonexistent-room",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_duplicate_active_listing_rejected(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data())
        # User already has an active listing
        existing = _make_doc_snapshot(
            "existing-listing",
            make_listing_data(owner_uid="test-uid-123", status="OPEN"),
        )
        mock_db.register_collection_docs("listings", [existing])

        resp = await client.post("/api/v1/listings/lease-transfer", json={
            "room_id": "room-1",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
        })
        assert resp.status_code == 409


class TestCreateSwapRequest:
    @pytest.mark.asyncio
    async def test_create_swap_request(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data(category="PARK_SHARED_2BR"))
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/swap-request", json={
            "room_id": "room-1",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
            "description": "Want to swap to category B",
            "desired_categories": ["ILANOT_STUDIO"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["listing_type"] == "SWAP_REQUEST"
        assert data["status"] == "OPEN"
        assert data["desired_categories"] == ["ILANOT_STUDIO"]

    @pytest.mark.asyncio
    async def test_swap_no_desired_categories(self, client, mock_db):
        mock_db.register_doc("rooms", "room-1", make_room_data())
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/swap-request", json={
            "room_id": "room-1",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
            "desired_categories": [],
        })
        assert resp.status_code == 400


class TestGetListing:
    @pytest.mark.asyncio
    async def test_get_listing(self, client, mock_db):
        mock_db.register_doc(
            "listings", "listing-1", make_listing_data()
        )

        resp = await client.get("/api/v1/listings/listing-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "listing-1"
        assert data["listing_type"] == "LEASE_TRANSFER"

    @pytest.mark.asyncio
    async def test_get_listing_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/listings/nonexistent")
        assert resp.status_code == 404


class TestCancelListing:
    @pytest.mark.asyncio
    async def test_cancel_open_listing(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)
        mock_db.register_collection_docs("matches", [])

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_cancel_other_users_listing_forbidden(self, client, mock_db):
        listing = make_listing_data(owner_uid="other-user", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_completed_listing_fails(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="COMPLETED")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 409


class TestBrowseListings:
    @pytest.mark.asyncio
    async def test_browse_returns_paginated(self, client, mock_db):
        listings = [
            _make_doc_snapshot(f"listing-{i}", make_listing_data())
            for i in range(3)
        ]
        mock_db.register_collection_docs("listings", listings)

        resp = await client.get("/api/v1/listings")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "has_next" in data

    @pytest.mark.asyncio
    async def test_browse_with_filters(self, client, mock_db):
        mock_db.register_collection_docs("listings", [])

        resp = await client.get(
            "/api/v1/listings?type=LEASE_TRANSFER&category=A&building=Building+3"
        )
        assert resp.status_code == 200


class TestMyListings:
    @pytest.mark.asyncio
    async def test_get_my_listings(self, client, mock_db):
        listings = [
            _make_doc_snapshot("listing-1", make_listing_data(owner_uid="test-uid-123"))
        ]
        mock_db.register_collection_docs("listings", listings)

        resp = await client.get("/api/v1/listings/my")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
