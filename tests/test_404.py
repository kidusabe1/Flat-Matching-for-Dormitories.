"""Tests for 404 handling on undefined API routes."""

import pytest


class TestUndefinedRoutes:
    @pytest.mark.asyncio
    async def test_undefined_api_route_returns_404(self, client):
        resp = await client.get("/api/v1/nonexistent-endpoint")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_undefined_nested_route_returns_404(self, client):
        resp = await client.get("/api/v1/listings/some-id/nonexistent")
        assert resp.status_code == 404
