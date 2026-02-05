from app.models.enums import LeaseTransferStatus

LEASE_TRANSFER_TRANSITIONS: dict[LeaseTransferStatus, set[LeaseTransferStatus]] = {
    LeaseTransferStatus.OPEN: {
        LeaseTransferStatus.MATCHED,
        LeaseTransferStatus.PENDING_APPROVAL,  # bidding: accept a bid directly
        LeaseTransferStatus.CANCELLED,
        LeaseTransferStatus.EXPIRED,
    },
    LeaseTransferStatus.MATCHED: {
        LeaseTransferStatus.PENDING_APPROVAL,
        LeaseTransferStatus.OPEN,  # reject/expire match -> reopen
        LeaseTransferStatus.CANCELLED,
    },
    LeaseTransferStatus.PENDING_APPROVAL: {
        LeaseTransferStatus.COMPLETED,
        LeaseTransferStatus.CANCELLED,
    },
    LeaseTransferStatus.COMPLETED: set(),
    LeaseTransferStatus.CANCELLED: set(),
    LeaseTransferStatus.EXPIRED: set(),
}


def validate_lease_transfer_transition(
    current: LeaseTransferStatus, target: LeaseTransferStatus
) -> bool:
    return target in LEASE_TRANSFER_TRANSITIONS.get(current, set())
