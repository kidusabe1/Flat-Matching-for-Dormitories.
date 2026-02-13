"""Tests for transaction confirm/cancel happy paths."""

import pytest

from tests.conftest import (
    make_match_data,
    make_room_data,
    make_transaction_data,
)


class TestConfirmLeaseTransfer:
    @pytest.mark.asyncio
    async def test_confirm_lease_transfer(self, client, mock_db):
        """From-user confirms a PENDING lease transfer transaction."""
        tx = make_transaction_data(
            transaction_type="LEASE_TRANSFER",
            status="PENDING",
            from_uid="test-uid-123",
            to_uid="test-uid-456",
            room_id="room-1",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        # Room with current occupant = from_uid
        mock_db.register_doc("rooms", "room-1", make_room_data(occupant_uid="test-uid-123"))

        # Match and listing for the cascade
        match = make_match_data(status="ACCEPTED", listing_id="listing-1")
        mock_db.register_doc("matches", "match-1", match)
        from tests.conftest import make_listing_data
        mock_db.register_doc("listings", "listing-1", make_listing_data(status="PENDING_APPROVAL"))

        # Empty stream for "cancel other pending transactions"
        mock_db.register_collection_docs("transactions", [])

        resp = await client.post("/api/v1/transactions/tx-1/confirm")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_confirm_not_party_forbidden(self, client, mock_db):
        """Non-involved user cannot confirm."""
        tx = make_transaction_data(
            status="PENDING",
            from_uid="user-A",
            to_uid="user-B",  # Neither is test-uid-123
        )
        mock_db.register_doc("transactions", "tx-1", tx)
        mock_db.register_doc("rooms", "room-1", make_room_data())

        resp = await client.post("/api/v1/transactions/tx-1/confirm")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_confirm_non_pending_fails(self, client, mock_db):
        """Cannot confirm an already COMPLETED transaction."""
        tx = make_transaction_data(
            status="COMPLETED",
            from_uid="test-uid-123",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        resp = await client.post("/api/v1/transactions/tx-1/confirm")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_confirm_transaction_not_found(self, client, mock_db):
        resp = await client.post("/api/v1/transactions/nonexistent/confirm")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_confirm_room_occupant_changed(self, client, mock_db):
        """Stale guard: room occupant changed since transaction was created."""
        tx = make_transaction_data(
            status="PENDING",
            from_uid="test-uid-123",
            to_uid="test-uid-456",
            room_id="room-1",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        # Room now occupied by someone else (not from_uid)
        mock_db.register_doc("rooms", "room-1", make_room_data(occupant_uid="intruder-uid"))

        resp = await client.post("/api/v1/transactions/tx-1/confirm")
        assert resp.status_code == 409


class TestCancelTransaction:
    @pytest.mark.asyncio
    async def test_cancel_pending_transaction(self, client, mock_db):
        """Party cancels a PENDING transaction."""
        tx = make_transaction_data(
            status="PENDING",
            from_uid="test-uid-123",
            to_uid="test-uid-456",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        # Matching match and listing for the cascade
        match = make_match_data(status="ACCEPTED", listing_id="listing-1")
        mock_db.register_doc("matches", "match-1", match)
        from tests.conftest import make_listing_data
        mock_db.register_doc("listings", "listing-1", make_listing_data(status="PENDING_APPROVAL"))

        resp = await client.post("/api/v1/transactions/tx-1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_cancel_completed_transaction_fails(self, client, mock_db):
        """Cannot cancel a COMPLETED transaction."""
        tx = make_transaction_data(
            status="COMPLETED",
            from_uid="test-uid-123",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        resp = await client.post("/api/v1/transactions/tx-1/cancel")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_cancel_not_party_forbidden(self, client, mock_db):
        """Non-involved user cannot cancel."""
        tx = make_transaction_data(
            status="PENDING",
            from_uid="user-A",
            to_uid="user-B",
        )
        mock_db.register_doc("transactions", "tx-1", tx)

        resp = await client.post("/api/v1/transactions/tx-1/cancel")
        assert resp.status_code == 403
