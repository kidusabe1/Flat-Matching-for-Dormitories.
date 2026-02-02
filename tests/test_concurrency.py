"""Tests for concurrency-related scenarios.

These tests verify the logical guards that prevent race conditions.
Full integration tests would require the Firestore emulator.
"""

import pytest

from app.middleware.error_handler import BadRequestError, ConflictError
from app.models.enums import LeaseTransferStatus, SwapRequestStatus
from app.state_machine.listing_states import validate_lease_transfer_transition
from app.state_machine.swap_states import validate_swap_transition


class TestConcurrencyGuards:
    def test_matched_listing_cannot_be_claimed_again(self):
        """Once a listing is MATCHED, it cannot transition to MATCHED again."""
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.MATCHED, LeaseTransferStatus.MATCHED
        ) is False

    def test_completed_listing_cannot_be_claimed(self):
        """COMPLETED listing cannot be claimed."""
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.COMPLETED, LeaseTransferStatus.MATCHED
        ) is False

    def test_cancelled_listing_cannot_be_claimed(self):
        """CANCELLED listing cannot be claimed."""
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.CANCELLED, LeaseTransferStatus.MATCHED
        ) is False

    def test_fully_matched_swap_cannot_be_fully_matched_again(self):
        """FULLY_MATCHED swap cannot be claimed by another user."""
        assert validate_swap_transition(
            SwapRequestStatus.FULLY_MATCHED, SwapRequestStatus.FULLY_MATCHED
        ) is False

    def test_version_field_prevents_stale_writes(self):
        """Demonstrate that our data model includes version fields for optimistic locking."""
        from tests.conftest import make_listing_data
        listing = make_listing_data()
        assert listing["version"] == 1
        # After claim, version should be incremented (this is tested in the service layer)

    def test_terminal_states_block_all_transitions(self):
        """No transitions are possible from terminal states."""
        for terminal in (
            LeaseTransferStatus.COMPLETED,
            LeaseTransferStatus.CANCELLED,
            LeaseTransferStatus.EXPIRED,
        ):
            for target in LeaseTransferStatus:
                assert validate_lease_transfer_transition(terminal, target) is False

        for terminal in (
            SwapRequestStatus.COMPLETED,
            SwapRequestStatus.CANCELLED,
            SwapRequestStatus.EXPIRED,
        ):
            for target in SwapRequestStatus:
                assert validate_swap_transition(terminal, target) is False
