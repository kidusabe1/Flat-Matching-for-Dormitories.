"""System test: Auth enforcement on all protected endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.services.firestore_client import get_db


class TestAuthEnforcement:
    """Verify every protected endpoint rejects unauthenticated requests."""

    @pytest.fixture
    def unauthenticated_app(self, mock_db):
        """App WITHOUT dependency override for get_current_user — no auth."""
        application = create_app()
        application.dependency_overrides[get_db] = lambda: mock_db
        # Note: No override for get_current_user → real auth check fires
        return application

    @pytest.fixture
    async def unauthenticated_client(self, unauthenticated_app):
        async with AsyncClient(
            transport=ASGITransport(app=unauthenticated_app),
            base_url="http://test",
        ) as c:
            yield c

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/rooms"),
        ("POST", "/api/v1/rooms"),
        ("GET", "/api/v1/rooms/any-id"),
        ("PUT", "/api/v1/rooms/any-id"),
        ("GET", "/api/v1/listings"),
        ("POST", "/api/v1/listings/lease-transfer"),
        ("POST", "/api/v1/listings/swap-request"),
        ("GET", "/api/v1/listings/my"),
        ("GET", "/api/v1/listings/any-id"),
        ("PUT", "/api/v1/listings/any-id"),
        ("POST", "/api/v1/listings/any-id/cancel"),
        ("POST", "/api/v1/listings/any-id/claim"),
        ("GET", "/api/v1/listings/any-id/bids"),
        ("GET", "/api/v1/matches/my"),
        ("GET", "/api/v1/matches/any-id"),
        ("POST", "/api/v1/matches/any-id/accept"),
        ("POST", "/api/v1/matches/any-id/reject"),
        ("POST", "/api/v1/matches/any-id/cancel"),
        ("GET", "/api/v1/matches/any-id/contact"),
        ("GET", "/api/v1/transactions/my"),
        ("GET", "/api/v1/transactions/any-id"),
        ("POST", "/api/v1/transactions/any-id/confirm"),
        ("POST", "/api/v1/transactions/any-id/cancel"),
        ("GET", "/api/v1/users/me"),
        ("POST", "/api/v1/users/profile"),
        ("PUT", "/api/v1/users/me"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    async def test_protected_endpoint_rejects_unauthenticated(
        self, unauthenticated_client, method, path
    ):
        """Every protected endpoint should return 401 or 403 without auth."""
        resp = await unauthenticated_client.request(method, path)
        assert resp.status_code in (401, 403), (
            f"{method} {path} returned {resp.status_code}, expected 401/403"
        )

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, unauthenticated_client):
        """Health check should work without authentication."""
        resp = await unauthenticated_client.get("/health")
        assert resp.status_code == 200
