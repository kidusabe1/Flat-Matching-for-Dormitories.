"""Tests for auth (email verification) API routes."""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest


class TestSendVerification:
    @pytest.mark.asyncio
    async def test_send_verification_pin(self, client, mock_db):
        with patch(
            "app.services.verification_service.send_verification_email",
            new_callable=AsyncMock,
        ) as mock_email:
            resp = await client.post("/api/v1/auth/send-verification")
            assert resp.status_code == 200
            data = resp.json()
            assert data["verified"] is False
            mock_email.assert_called_once()
            # Email should be sent to the test user
            assert mock_email.call_args[0][0] == "test@biu.ac.il"
            # PIN should be 6 digits
            pin = mock_email.call_args[0][1]
            assert len(pin) == 6
            assert pin.isdigit()

    @pytest.mark.asyncio
    async def test_resend_reuses_existing_valid_pin(self, client, mock_db):
        existing_pin = "123456"
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": existing_pin,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                "verified": False,
            },
        )

        with patch(
            "app.services.verification_service.send_verification_email",
            new_callable=AsyncMock,
        ) as mock_email:
            resp = await client.post("/api/v1/auth/send-verification")
            assert resp.status_code == 200
            # Should reuse the existing PIN, not generate a new one
            mock_email.assert_called_once_with("test@biu.ac.il", existing_pin)

    @pytest.mark.asyncio
    async def test_resend_generates_new_pin_when_expired(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "999999",
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=20),
                "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10),
                "verified": False,
            },
        )

        with patch(
            "app.services.verification_service.send_verification_email",
            new_callable=AsyncMock,
        ) as mock_email:
            resp = await client.post("/api/v1/auth/send-verification")
            assert resp.status_code == 200
            # Should generate a NEW pin since old one expired
            pin = mock_email.call_args[0][1]
            assert pin != "999999"


class TestVerifyPin:
    @pytest.mark.asyncio
    async def test_verify_correct_pin(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
                "verified": False,
            },
        )

        resp = await client.post(
            "/api/v1/auth/verify-pin", json={"pin": "654321"}
        )
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    @pytest.mark.asyncio
    async def test_verify_incorrect_pin(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
                "verified": False,
            },
        )

        resp = await client.post(
            "/api/v1/auth/verify-pin", json={"pin": "000000"}
        )
        assert resp.status_code == 409
        assert "Incorrect PIN" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_expired_pin(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=20),
                "expires_at": datetime.now(timezone.utc) - timedelta(minutes=10),
                "verified": False,
            },
        )

        resp = await client.post(
            "/api/v1/auth/verify-pin", json={"pin": "654321"}
        )
        assert resp.status_code == 409
        assert "expired" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_already_verified(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
                "verified": True,
            },
        )

        resp = await client.post(
            "/api/v1/auth/verify-pin", json={"pin": "654321"}
        )
        assert resp.status_code == 409
        assert "already verified" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_no_pin_found(self, client, mock_db):
        # No verification doc registered
        resp = await client.post(
            "/api/v1/auth/verify-pin", json={"pin": "123456"}
        )
        assert resp.status_code == 404


class TestVerificationStatus:
    @pytest.mark.asyncio
    async def test_status_verified(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "verified": True,
            },
        )

        resp = await client.get("/api/v1/auth/verification-status")
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    @pytest.mark.asyncio
    async def test_status_not_verified(self, client, mock_db):
        mock_db.register_doc(
            "email_verifications",
            "test-uid-123",
            {
                "email": "test@biu.ac.il",
                "pin": "654321",
                "verified": False,
            },
        )

        resp = await client.get("/api/v1/auth/verification-status")
        assert resp.status_code == 200
        assert resp.json()["verified"] is False

    @pytest.mark.asyncio
    async def test_status_no_record(self, client, mock_db):
        # No verification doc -> not verified
        resp = await client.get("/api/v1/auth/verification-status")
        assert resp.status_code == 200
        assert resp.json()["verified"] is False
