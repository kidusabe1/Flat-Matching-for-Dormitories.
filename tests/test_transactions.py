"""Tests for transaction API routes."""

import pytest

from tests.conftest import make_transaction_data


class TestGetTransaction:
    @pytest.mark.asyncio
    async def test_get_transaction(self, client, mock_db):
        tx = make_transaction_data()
        mock_db.register_doc("transactions", "tx-1", tx)

        resp = await client.get("/api/v1/transactions/tx-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "tx-1"
        assert data["status"] == "PENDING"
        assert data["transaction_type"] == "LEASE_TRANSFER"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client, mock_db):
        resp = await client.get("/api/v1/transactions/nonexistent")
        assert resp.status_code == 404


class TestGetMyTransactions:
    @pytest.mark.asyncio
    async def test_get_my_transactions(self, client, mock_db):
        tx = make_transaction_data(from_uid="test-uid-123")
        snap = pytest.importorskip("tests.conftest")
        from tests.conftest import _make_doc_snapshot
        tx_snap = _make_doc_snapshot("tx-1", tx)
        mock_db.register_collection_docs("transactions", [tx_snap])

        resp = await client.get("/api/v1/transactions/my")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_my_transactions_with_status(self, client, mock_db):
        mock_db.register_collection_docs("transactions", [])

        resp = await client.get("/api/v1/transactions/my?status=COMPLETED")
        assert resp.status_code == 200


class TestCancelTransaction:
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_transaction(self, client, mock_db):
        resp = await client.post("/api/v1/transactions/nonexistent/cancel")
        assert resp.status_code == 404
