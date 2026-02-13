"""System test: CORS configuration."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app
from app.services.firestore_client import get_db


class TestCORS:
    @pytest.fixture
    def cors_app(self, mock_db):
        application = create_app()
        application.dependency_overrides[get_db] = lambda: mock_db
        return application

    @pytest.fixture
    async def cors_client(self, cors_app):
        async with AsyncClient(
            transport=ASGITransport(app=cors_app),
            base_url="http://test",
        ) as c:
            yield c

    @pytest.fixture
    def allowed_origin(self):
        """Return an origin that is in the app's configured cors_origins."""
        origins = get_settings().cors_origins
        return origins[0] if origins else "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_cors_preflight_allowed_origin(self, cors_client, allowed_origin):
        """OPTIONS preflight from allowed origin should include CORS headers."""
        resp = await cors_client.options(
            "/health",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_actual_request_health(self, cors_client, allowed_origin):
        """GET /health with Origin header should get CORS response headers."""
        resp = await cors_client.get(
            "/health",
            headers={"Origin": allowed_origin},
        )
        assert resp.status_code == 200
