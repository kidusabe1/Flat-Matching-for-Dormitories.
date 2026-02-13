"""Integration tests for notification triggers."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.enums import LeaseTransferStatus, ListingType, MatchStatus, SwapRequestStatus
from app.services import listing_service, match_service


@pytest.fixture
def mock_notifications():
    """Mock all notification service functions."""
    with patch("app.services.notification_service.notify_new_bid", new_callable=AsyncMock) as mock_new, \
         patch("app.services.notification_service.notify_swap_bid", new_callable=AsyncMock) as mock_swap, \
         patch("app.services.notification_service.notify_bid_accepted", new_callable=AsyncMock) as mock_accept, \
         patch("app.services.notification_service.notify_bid_rejected", new_callable=AsyncMock) as mock_reject:
        yield {
            "new_bid": mock_new,
            "swap_bid": mock_swap,
            "bid_accepted": mock_accept,
            "bid_rejected": mock_reject,
        }


@pytest.mark.asyncio
async def test_claim_listing_triggers_notification(mock_db, mock_notifications):
    """Verify claim_listing triggers notify_new_bid."""
    # Setup listing
    listing_id = "list-1"
    owner_uid = "owner-123"
    claimant_uid = "claimant-456"

    mock_db.register_doc(
        "listings",
        listing_id,
        {
            "status": LeaseTransferStatus.OPEN.value,
            "owner_uid": owner_uid,
            "listing_type": ListingType.LEASE_TRANSFER.value,
            "room_id": "room-1",
            "room_building": "Building A",
            "room_category": "Type A",
        },
    )

    # Act
    await listing_service.claim_listing(mock_db, listing_id, claimant_uid)

    # Assert
    import asyncio
    await asyncio.sleep(0)  # Yield to allow task to start

    mock_notifications["new_bid"].assert_called_once()
    call_args = mock_notifications["new_bid"].call_args
    assert call_args.kwargs["owner_uid"] == owner_uid
    assert call_args.kwargs["claimant_uid"] == claimant_uid
    assert call_args.kwargs["listing_id"] == listing_id


@pytest.mark.asyncio
async def test_claim_swap_triggers_notification(mock_db, mock_notifications):
    """Verify claim_swap triggers notify_swap_bid."""
    listing_id = "list-target"
    claimant_listing_id = "list-source"
    owner_uid = "owner-123"
    claimant_uid = "claimant-456"

    # Setup listings
    mock_db.register_doc(
        "listings",
        listing_id,
        {
            "status": SwapRequestStatus.OPEN.value,
            "owner_uid": owner_uid,
            "listing_type": ListingType.SWAP_REQUEST.value,
            "room_id": "room-1",
            "room_category": "Type A",
            "room_building": "Building A",
            "desired_categories": ["Type B"],
        },
    )
    mock_db.register_doc(
        "listings",
        claimant_listing_id,
        {
            "status": SwapRequestStatus.OPEN.value,
            "owner_uid": claimant_uid,
            "listing_type": ListingType.SWAP_REQUEST.value,
            "room_id": "room-2",
            "room_category": "Type B",
            "room_building": "Building B",
            "desired_categories": ["Type A"],
        },
    )

    # Act
    await listing_service.claim_swap(mock_db, listing_id, claimant_uid, claimant_listing_id)

    import asyncio
    await asyncio.sleep(0)

    mock_notifications["swap_bid"].assert_called_once()
    assert mock_notifications["swap_bid"].call_args.kwargs["owner_uid"] == owner_uid


@pytest.mark.asyncio
async def test_accept_match_triggers_notification(mock_db, mock_notifications):
    """Verify accept_match triggers notify_bid_accepted."""
    match_id = "match-1"
    owner_uid = "owner-123"
    claimant_uid = "claimant-456"

    # Setup match and listing
    mock_db.register_doc(
        "matches",
        match_id,
        {
            "status": MatchStatus.PROPOSED.value,
            "listing_id": "list-1",
            "claimant_uid": claimant_uid,
            "match_type": ListingType.LEASE_TRANSFER.value,
            "offered_room_building": "Building A",
            "offered_room_id": "room-1",
            "offered_room_category": "Type A",
        },
    )
    mock_db.register_doc(
        "listings",
        "list-1",
        {
            "status": LeaseTransferStatus.OPEN.value,
            "owner_uid": owner_uid,
            "listing_type": ListingType.LEASE_TRANSFER.value,
            "room_id": "room-1",
            "lease_start_date": None,
            "lease_end_date": None,
            "version": 1,
        },
    )

    # Act
    await match_service.accept_match(mock_db, match_id, owner_uid)

    import asyncio
    await asyncio.sleep(0)

    mock_notifications["bid_accepted"].assert_called_once()
    assert mock_notifications["bid_accepted"].call_args.kwargs["claimant_uid"] == claimant_uid


@pytest.mark.asyncio
async def test_reject_match_triggers_notification(mock_db, mock_notifications):
    """Verify reject_match triggers notify_bid_rejected."""
    match_id = "match-1"
    owner_uid = "owner-123"
    claimant_uid = "claimant-456"

    # Setup match and listing
    mock_db.register_doc(
        "matches",
        match_id,
        {
            "status": MatchStatus.PROPOSED.value,
            "match_type": ListingType.LEASE_TRANSFER.value,
            "listing_id": "list-1",
            "claimant_uid": claimant_uid,
            "offered_room_id": "room-1",
            "offered_room_category": "Type A",
            "offered_room_building": "Building A",
        },
    )
    mock_db.register_doc(
        "listings",
        "list-1",
        {
            "status": LeaseTransferStatus.OPEN.value,
            "owner_uid": owner_uid,
            "listing_type": ListingType.LEASE_TRANSFER.value,
            "version": 1,
        },
    )

    # Act
    await match_service.reject_match(mock_db, match_id, owner_uid)

    import asyncio
    await asyncio.sleep(0)

    mock_notifications["bid_rejected"].assert_called_once()
    assert mock_notifications["bid_rejected"].call_args.kwargs["claimant_uid"] == claimant_uid
