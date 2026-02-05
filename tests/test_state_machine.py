"""Tests for state machine transition validation."""

import pytest

from app.middleware.error_handler import InvalidTransitionError
from app.models.enums import LeaseTransferStatus, SwapRequestStatus
from app.state_machine.listing_states import validate_lease_transfer_transition
from app.state_machine.swap_states import validate_swap_transition
from app.state_machine.transitions import assert_transition, validate_transition


# ──────────────────────────────────────────────────────────
# Lease Transfer State Machine
# ──────────────────────────────────────────────────────────

class TestLeaseTransferTransitions:
    def test_open_to_matched(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.OPEN, LeaseTransferStatus.MATCHED
        ) is True

    def test_open_to_cancelled(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.OPEN, LeaseTransferStatus.CANCELLED
        ) is True

    def test_open_to_expired(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.OPEN, LeaseTransferStatus.EXPIRED
        ) is True

    def test_matched_to_pending_approval(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.MATCHED, LeaseTransferStatus.PENDING_APPROVAL
        ) is True

    def test_matched_to_open_on_reject(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.MATCHED, LeaseTransferStatus.OPEN
        ) is True

    def test_matched_to_cancelled(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.MATCHED, LeaseTransferStatus.CANCELLED
        ) is True

    def test_pending_approval_to_completed(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.PENDING_APPROVAL, LeaseTransferStatus.COMPLETED
        ) is True

    def test_pending_approval_to_cancelled(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.PENDING_APPROVAL, LeaseTransferStatus.CANCELLED
        ) is True

    # Invalid transitions
    def test_completed_is_terminal(self):
        for target in LeaseTransferStatus:
            if target != LeaseTransferStatus.COMPLETED:
                assert validate_lease_transfer_transition(
                    LeaseTransferStatus.COMPLETED, target
                ) is False

    def test_cancelled_is_terminal(self):
        for target in LeaseTransferStatus:
            if target != LeaseTransferStatus.CANCELLED:
                assert validate_lease_transfer_transition(
                    LeaseTransferStatus.CANCELLED, target
                ) is False

    def test_expired_is_terminal(self):
        for target in LeaseTransferStatus:
            if target != LeaseTransferStatus.EXPIRED:
                assert validate_lease_transfer_transition(
                    LeaseTransferStatus.EXPIRED, target
                ) is False

    def test_open_cannot_skip_to_completed(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.OPEN, LeaseTransferStatus.COMPLETED
        ) is False

    def test_open_to_pending_approval_for_bidding(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.OPEN, LeaseTransferStatus.PENDING_APPROVAL
        ) is True

    def test_matched_cannot_go_to_expired(self):
        assert validate_lease_transfer_transition(
            LeaseTransferStatus.MATCHED, LeaseTransferStatus.EXPIRED
        ) is False


# ──────────────────────────────────────────────────────────
# Swap Request State Machine
# ──────────────────────────────────────────────────────────

class TestSwapTransitions:
    def test_open_to_partial_match(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.PARTIAL_MATCH
        ) is True

    def test_open_to_fully_matched(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.FULLY_MATCHED
        ) is True

    def test_open_to_cancelled(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.CANCELLED
        ) is True

    def test_open_to_expired(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.EXPIRED
        ) is True

    def test_partial_to_fully_matched(self):
        assert validate_swap_transition(
            SwapRequestStatus.PARTIAL_MATCH, SwapRequestStatus.FULLY_MATCHED
        ) is True

    def test_partial_to_open_on_reject(self):
        assert validate_swap_transition(
            SwapRequestStatus.PARTIAL_MATCH, SwapRequestStatus.OPEN
        ) is True

    def test_partial_to_cancelled(self):
        assert validate_swap_transition(
            SwapRequestStatus.PARTIAL_MATCH, SwapRequestStatus.CANCELLED
        ) is True

    def test_partial_to_expired(self):
        assert validate_swap_transition(
            SwapRequestStatus.PARTIAL_MATCH, SwapRequestStatus.EXPIRED
        ) is True

    def test_fully_matched_to_pending_approval(self):
        assert validate_swap_transition(
            SwapRequestStatus.FULLY_MATCHED, SwapRequestStatus.PENDING_APPROVAL
        ) is True

    def test_fully_matched_to_partial_match(self):
        assert validate_swap_transition(
            SwapRequestStatus.FULLY_MATCHED, SwapRequestStatus.PARTIAL_MATCH
        ) is True

    def test_fully_matched_to_cancelled(self):
        assert validate_swap_transition(
            SwapRequestStatus.FULLY_MATCHED, SwapRequestStatus.CANCELLED
        ) is True

    def test_pending_approval_to_completed(self):
        assert validate_swap_transition(
            SwapRequestStatus.PENDING_APPROVAL, SwapRequestStatus.COMPLETED
        ) is True

    def test_pending_approval_to_cancelled(self):
        assert validate_swap_transition(
            SwapRequestStatus.PENDING_APPROVAL, SwapRequestStatus.CANCELLED
        ) is True

    # Invalid transitions
    def test_completed_is_terminal(self):
        for target in SwapRequestStatus:
            if target != SwapRequestStatus.COMPLETED:
                assert validate_swap_transition(
                    SwapRequestStatus.COMPLETED, target
                ) is False

    def test_cancelled_is_terminal(self):
        for target in SwapRequestStatus:
            if target != SwapRequestStatus.CANCELLED:
                assert validate_swap_transition(
                    SwapRequestStatus.CANCELLED, target
                ) is False

    def test_open_cannot_skip_to_completed(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.COMPLETED
        ) is False

    def test_open_to_pending_approval_for_bidding(self):
        assert validate_swap_transition(
            SwapRequestStatus.OPEN, SwapRequestStatus.PENDING_APPROVAL
        ) is True

    def test_partial_cannot_skip_to_pending_approval(self):
        assert validate_swap_transition(
            SwapRequestStatus.PARTIAL_MATCH, SwapRequestStatus.PENDING_APPROVAL
        ) is False


# ──────────────────────────────────────────────────────────
# Unified Transition Helper
# ──────────────────────────────────────────────────────────

class TestTransitionHelper:
    def test_validate_lease_transfer(self):
        assert validate_transition("LEASE_TRANSFER", "OPEN", "MATCHED") is True
        assert validate_transition("LEASE_TRANSFER", "COMPLETED", "OPEN") is False

    def test_validate_swap_request(self):
        assert validate_transition("SWAP_REQUEST", "OPEN", "PARTIAL_MATCH") is True
        assert validate_transition("SWAP_REQUEST", "COMPLETED", "OPEN") is False

    def test_validate_unknown_type(self):
        assert validate_transition("UNKNOWN", "OPEN", "MATCHED") is False

    def test_assert_transition_valid(self):
        # Should not raise
        assert_transition("LEASE_TRANSFER", "OPEN", "MATCHED")

    def test_assert_transition_invalid(self):
        with pytest.raises(InvalidTransitionError):
            assert_transition("LEASE_TRANSFER", "COMPLETED", "OPEN")
