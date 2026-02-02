from app.models.enums import SwapRequestStatus

SWAP_REQUEST_TRANSITIONS: dict[SwapRequestStatus, set[SwapRequestStatus]] = {
    SwapRequestStatus.OPEN: {
        SwapRequestStatus.PARTIAL_MATCH,
        SwapRequestStatus.FULLY_MATCHED,  # direct swap: both sides at once
        SwapRequestStatus.CANCELLED,
        SwapRequestStatus.EXPIRED,
    },
    SwapRequestStatus.PARTIAL_MATCH: {
        SwapRequestStatus.FULLY_MATCHED,
        SwapRequestStatus.OPEN,  # partial match rejected -> reopen
        SwapRequestStatus.CANCELLED,
        SwapRequestStatus.EXPIRED,
    },
    SwapRequestStatus.FULLY_MATCHED: {
        SwapRequestStatus.PENDING_APPROVAL,
        SwapRequestStatus.PARTIAL_MATCH,  # one match fails, keep the other
        SwapRequestStatus.CANCELLED,
    },
    SwapRequestStatus.PENDING_APPROVAL: {
        SwapRequestStatus.COMPLETED,
        SwapRequestStatus.CANCELLED,
    },
    SwapRequestStatus.COMPLETED: set(),
    SwapRequestStatus.CANCELLED: set(),
    SwapRequestStatus.EXPIRED: set(),
}


def validate_swap_transition(
    current: SwapRequestStatus, target: SwapRequestStatus
) -> bool:
    return target in SWAP_REQUEST_TRANSITIONS.get(current, set())
