"""System test: Error handling and response format consistency."""

import pytest


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_not_found_returns_detail(self, client, mock_db):
        """404 responses should return {"detail": "..."} format."""
        resp = await client.get("/api/v1/listings/nonexistent")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_forbidden_returns_detail(self, client, mock_db):
        from tests.conftest import make_listing_data
        listing = make_listing_data(owner_uid="other-user", status="OPEN")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 403
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_conflict_returns_detail(self, client, mock_db):
        from tests.conftest import make_listing_data
        listing = make_listing_data(owner_uid="test-uid-123", status="COMPLETED")
        mock_db.register_doc("listings", "listing-1", listing)

        resp = await client.post("/api/v1/listings/listing-1/cancel")
        assert resp.status_code == 409
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client, mock_db):
        """Invalid payload should return 422 with validation details."""
        resp = await client.post("/api/v1/listings/lease-transfer", json={
            # Missing required fields
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self, client):
        """Non-existent API route returns 404."""
        resp = await client.get("/api/v1/nonexistent-route")
        assert resp.status_code == 404


class TestResponseFormats:
    @pytest.mark.asyncio
    async def test_listing_response_has_required_fields(self, client, mock_db):
        """Listing responses should contain all expected fields."""
        from tests.conftest import make_listing_data
        mock_db.register_doc("listings", "listing-1", make_listing_data())

        resp = await client.get("/api/v1/listings/listing-1")
        assert resp.status_code == 200
        data = resp.json()
        required = [
            "id", "listing_type", "status", "owner_uid",
            "room_id", "room_category", "room_building",
            "lease_start_date", "lease_end_date", "description",
        ]
        for field in required:
            assert field in data, f"Missing {field}"

    @pytest.mark.asyncio
    async def test_transaction_response_has_required_fields(self, client, mock_db):
        """Transaction responses should contain all expected fields."""
        from tests.conftest import make_transaction_data
        mock_db.register_doc("transactions", "tx-1", make_transaction_data())

        resp = await client.get("/api/v1/transactions/tx-1")
        assert resp.status_code == 200
        data = resp.json()
        required = [
            "id", "transaction_type", "status",
            "lease_start_date", "lease_end_date",
        ]
        for field in required:
            assert field in data, f"Missing {field}"
