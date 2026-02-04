from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.main import create_app
from app.services.firestore_client import get_db


@pytest.fixture
def test_user():
    return FirebaseUser(uid="test-uid-123", email="test@biu.ac.il", name="Test Student")


@pytest.fixture
def test_user_b():
    return FirebaseUser(uid="test-uid-456", email="other@biu.ac.il", name="Other Student")


def _make_doc_snapshot(doc_id: str, data: dict | None, exists: bool = True):
    """Create a mock Firestore document snapshot."""
    snap = MagicMock()
    snap.id = doc_id
    snap.exists = exists
    snap.to_dict.return_value = data if exists else None
    return snap


def _make_async_stream(docs: list):
    """Create an async iterator from a list of document snapshots."""
    async def stream():
        for doc in docs:
            yield doc
    return stream()


@pytest.fixture
def mock_db():
    """Create a mock Firestore AsyncClient with chainable query support."""
    db = AsyncMock()

    # Store documents by collection/id for flexible mocking
    db._docs = {}
    db._collections = {}

    def setup_collection(name):
        collection = MagicMock()

        def document(doc_id=None):
            doc_ref = MagicMock()
            doc_ref.id = doc_id or f"auto-{name}-id"

            async def get_fn(transaction=None):
                key = f"{name}/{doc_ref.id}"
                if key in db._docs:
                    data, exists = db._docs[key]
                    return _make_doc_snapshot(doc_ref.id, data, exists)
                return _make_doc_snapshot(doc_ref.id, None, False)

            doc_ref.get = get_fn
            doc_ref.set = AsyncMock()
            doc_ref.update = AsyncMock()
            doc_ref.delete = AsyncMock()
            return doc_ref

        collection.document = document

        async def add_fn(data):
            doc_id = f"auto-{name}-id"
            ref = MagicMock()
            ref.id = doc_id
            return (None, ref)

        collection.add = add_fn

        # Query chaining
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

        async def stream_fn():
            for doc in db._collections.get(name, []):
                yield doc

        collection.stream = stream_fn

        return collection

    db.collection = lambda name: setup_collection(name)

    # Helper to register a document
    def register_doc(collection, doc_id, data, exists=True):
        db._docs[f"{collection}/{doc_id}"] = (data, exists)

    # Helper to register collection query results
    def register_collection_docs(collection, docs):
        db._collections[collection] = docs

    db.register_doc = register_doc
    db.register_collection_docs = register_collection_docs

    # Transaction support — must be compatible with @async_transactional
    def transaction():
        tx = MagicMock()
        tx.create = MagicMock()
        tx.update = MagicMock()
        tx.delete = MagicMock()
        tx._commit = AsyncMock()
        tx._rollback = AsyncMock()
        tx._begin = AsyncMock()
        tx._max_attempts = 1
        tx._read_only = False
        tx._id = b"mock-tx-id"
        tx.id = b"mock-tx-id"
        return tx

    db.transaction = transaction

    return db


@pytest.fixture
def app(mock_db, test_user):
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: test_user
    application.dependency_overrides[get_db] = lambda: mock_db
    return application


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


def make_room_data(
    category="PARK_SHARED_2BR",
    building="Building 3",
    floor=2,
    room_number="204",
    occupant_uid=None,
):
    return {
        "building": building,
        "floor": floor,
        "room_number": room_number,
        "category": category,
        "description": "Test room",
        "amenities": [],
        "occupant_uid": occupant_uid,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def make_listing_data(
    listing_type="LEASE_TRANSFER",
    status="OPEN",
    owner_uid="test-uid-123",
    room_id="room-1",
    room_category="PARK_SHARED_2BR",
    room_building="Building 3",
    version=1,
    **kwargs,
):
    now = datetime.now(timezone.utc)
    data = {
        "listing_type": listing_type,
        "status": status,
        "version": version,
        "owner_uid": owner_uid,
        "room_id": room_id,
        "room_category": room_category,
        "room_building": room_building,
        "lease_start_date": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "lease_end_date": datetime(2026, 8, 31, tzinfo=timezone.utc),
        "description": "Test listing",
        "asking_price": None,
        "move_in_date": None,
        "desired_categories": None,
        "desired_buildings": None,
        "desired_min_start": None,
        "desired_max_end": None,
        "replacement_match_id": None,
        "target_match_id": None,
        "expires_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return data


def make_match_data(
    match_type="LEASE_TRANSFER",
    status="PROPOSED",
    listing_id="listing-1",
    claimant_uid="test-uid-456",
    **kwargs,
):
    now = datetime.now(timezone.utc)
    data = {
        "match_type": match_type,
        "status": status,
        "listing_id": listing_id,
        "claimant_uid": claimant_uid,
        "claimant_listing_id": None,
        "offered_room_id": "room-1",
        "offered_room_category": "PARK_SHARED_2BR",
        "offered_room_building": "Building 3",
        "proposed_at": now,
        "responded_at": None,
        "expires_at": datetime(2026, 3, 3, tzinfo=timezone.utc),
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return data


def make_transaction_data(
    transaction_type="LEASE_TRANSFER",
    status="PENDING",
    **kwargs,
):
    now = datetime.now(timezone.utc)
    data = {
        "transaction_type": transaction_type,
        "status": status,
        "match_id": "match-1",
        "from_uid": "test-uid-123",
        "to_uid": "test-uid-456",
        "room_id": "room-1",
        "match_ids": None,
        "party_a_uid": None,
        "party_a_room_id": None,
        "party_b_uid": None,
        "party_b_room_id": None,
        "lease_start_date": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "lease_end_date": datetime(2026, 8, 31, tzinfo=timezone.utc),
        "initiated_at": now,
        "completed_at": None,
        "failed_at": None,
        "failure_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return data
