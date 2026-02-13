"""Tests for listing update route."""

import pytest

from tests.conftest import make_listing_data


class TestUpdateListing:
    @pytest.mark.asyncio
    async def test_update_open_listing(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "description": "Updated description",
            "asking_price": 500,
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_non_open_listing_fails(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="PENDING_APPROVAL")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "description": "Should fail",
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_update_other_users_listing_forbidden(self, client, mock_db):
        listing = make_listing_data(owner_uid="other-user", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "description": "Not mine",
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_listing_not_found(self, client, mock_db):
        resp = await client.put("/api/v1/listings/nonexistent", json={
            "description": "Ghost listing",
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_with_new_dates(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "lease_start_date": "2026-04-01",
            "lease_end_date": "2026-09-30",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_move_in_date(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "move_in_date": "2026-04-15",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_completed_listing_fails(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="COMPLETED")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "description": "Too late",
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_update_cancelled_listing_fails(self, client, mock_db):
        listing = make_listing_data(owner_uid="test-uid-123", status="CANCELLED")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.put("/api/v1/listings/listing-1", json={
            "description": "Already cancelled",
        })
        assert resp.status_code == 409
