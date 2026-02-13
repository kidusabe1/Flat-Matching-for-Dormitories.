"""Unit tests for the notification service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services import notification_service


@pytest.fixture
def mock_send_email():
    with patch("app.services.notification_service.send_html_email", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_db_with_users(mock_db):
    """Mock database with user email lookups."""
    # Setup mock users
    mock_db.register_doc(
        "users",
        "owner-123",
        {"email": "owner@biu.ac.il", "full_name": "Owner User"},
    )
    mock_db.register_doc(
        "users",
        "claimant-456",
        {"email": "claimant@biu.ac.il", "full_name": "Claimant User"},
    )
    # User without email
    mock_db.register_doc(
        "users",
        "no-email-789",
        {"full_name": "No Email User"},
    )
    return mock_db


@pytest.mark.asyncio
async def test_notify_new_bid(mock_db_with_users, mock_send_email):
    """Test notifying listing owner of a new bid."""
    await notification_service.notify_new_bid(
        mock_db_with_users,
        owner_uid="owner-123",
        claimant_uid="claimant-456",
        listing_id="list-1",
        room_building="Building 1",
        room_number="101",
    )

    mock_send_email.assert_called_once()
    args = mock_send_email.call_args[0]
    assert args[0] == "owner@biu.ac.il"
    assert "New bid on your listing" in args[1]  # Subject
    assert "Claimant User" in args[2]  # Text body
    assert "Building 1 #101" in args[2]


@pytest.mark.asyncio
async def test_notify_new_bid_no_email(mock_db_with_users, mock_send_email):
    """Test that missing owner email gracefully aborts."""
    await notification_service.notify_new_bid(
        mock_db_with_users,
        owner_uid="no-email-789",
        claimant_uid="claimant-456",
        listing_id="list-1",
    )
    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_notify_swap_bid(mock_db_with_users, mock_send_email):
    """Test notifying listing owner of a swap proposal."""
    await notification_service.notify_swap_bid(
        mock_db_with_users,
        owner_uid="owner-123",
        claimant_uid="claimant-456",
        listing_id="list-1",
        offered_category="PARK_SHARED_2BR",
    )

    mock_send_email.assert_called_once()
    args = mock_send_email.call_args[0]
    assert args[0] == "owner@biu.ac.il"
    assert "swap proposal" in args[1]
    assert "PARK_SHARED_2BR" in args[2]


@pytest.mark.asyncio
async def test_notify_bid_accepted(mock_db_with_users, mock_send_email):
    """Test notifying claimant that their bid was accepted."""
    await notification_service.notify_bid_accepted(
        mock_db_with_users,
        claimant_uid="claimant-456",
        listing_id="list-1",
        room_building="Building 1",
        room_number="101",
    )

    mock_send_email.assert_called_once()
    args = mock_send_email.call_args[0]
    assert args[0] == "claimant@biu.ac.il"
    assert "bid was accepted" in args[1]
    assert "Building 1 #101" in args[2]


@pytest.mark.asyncio
async def test_notify_bid_rejected(mock_db_with_users, mock_send_email):
    """Test notifying claimant that their bid was rejected."""
    await notification_service.notify_bid_rejected(
        mock_db_with_users,
        claimant_uid="claimant-456",
        listing_id="list-1",
    )

    mock_send_email.assert_called_once()
    args = mock_send_email.call_args[0]
    assert args[0] == "claimant@biu.ac.il"
    assert "Bid update" in args[1]


@pytest.mark.asyncio
async def test_send_email_error_swallowed(mock_db_with_users, mock_send_email):
    """Test that email sending errors are logged but not raised."""
    mock_send_email.side_effect = RuntimeError("SMTP failed")

    # Should not raise exception
    await notification_service.notify_new_bid(
        mock_db_with_users,
        owner_uid="owner-123",
        claimant_uid="claimant-456",
        listing_id="list-1",
    )

    mock_send_email.assert_called_once()
