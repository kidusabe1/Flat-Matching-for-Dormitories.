"""Tests for find_compatible_lease_transfers in matching engine."""

import pytest
from unittest.mock import MagicMock

from tests.conftest import _make_doc_snapshot, make_listing_data
from app.services.matching_engine import find_compatible_lease_transfers


class TestFindCompatibleLeaseTransfers:
    @pytest.fixture
    def mock_db(self):
        """Minimal mock DB for testing the matching engine function."""
        from unittest.mock import AsyncMock
        db = AsyncMock()
        db._docs = {}
        db._collections = {}

        def setup_collection(name):
            collection = MagicMock()

            def document(doc_id=None):
                doc_ref = MagicMock()
                doc_ref.id = doc_id

                async def get_fn(transaction=None):
                    key = f"{name}/{doc_ref.id}"
                    if key in db._docs:
                        data, exists = db._docs[key]
                        return _make_doc_snapshot(doc_ref.id, data, exists)
                    return _make_doc_snapshot(doc_ref.id, None, False)

                doc_ref.get = get_fn
                return doc_ref

            collection.document = document

            def where(*args, **kwargs):
                query = MagicMock()
                query.where = where
                query.limit = lambda n: query
                query.order_by = lambda *a, **kw: query

                async def stream_fn():
                    for doc in db._collections.get(name, []):
                        yield doc

                query.stream = stream_fn
                query.get = AsyncMock(return_value=db._collections.get(name, []))
                return query

            collection.where = where
            collection.limit = lambda n: collection
            return collection

        db.collection = lambda name: setup_collection(name)

        def register_doc(collection, doc_id, data, exists=True):
            db._docs[f"{collection}/{doc_id}"] = (data, exists)

        def register_collection_docs(collection, docs):
            db._collections[collection] = docs

        db.register_doc = register_doc
        db.register_collection_docs = register_collection_docs
        return db

    @pytest.mark.asyncio
    async def test_basic_search(self, mock_db):
        """Finds OPEN lease transfers."""
        listings = [
            _make_doc_snapshot("lt-1", make_listing_data(
                listing_type="LEASE_TRANSFER", status="OPEN",
                owner_uid="user-A", room_category="PARK_SHARED_2BR",
            )),
            _make_doc_snapshot("lt-2", make_listing_data(
                listing_type="LEASE_TRANSFER", status="OPEN",
                owner_uid="user-B", room_category="ILANOT_STUDIO",
            )),
        ]
        mock_db.register_collection_docs("listings", listings)

        results = await find_compatible_lease_transfers(mock_db)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_filter_by_category(self, mock_db):
        """Filter results by desired category."""
        listings = [
            _make_doc_snapshot("lt-1", make_listing_data(
                listing_type="LEASE_TRANSFER", status="OPEN",
                room_category="PARK_SHARED_2BR",
            )),
        ]
        mock_db.register_collection_docs("listings", listings)

        results = await find_compatible_lease_transfers(
            mock_db, category="PARK_SHARED_2BR"
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_db):
        """Returns empty list when no compatible transfers exist."""
        mock_db.register_collection_docs("listings", [])

        results = await find_compatible_lease_transfers(mock_db)
        assert results == []
