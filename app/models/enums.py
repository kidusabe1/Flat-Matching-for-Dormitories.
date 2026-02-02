from enum import Enum


class RoomCategory(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class ListingType(str, Enum):
    LEASE_TRANSFER = "LEASE_TRANSFER"
    SWAP_REQUEST = "SWAP_REQUEST"


class LeaseTransferStatus(str, Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SwapRequestStatus(str, Enum):
    OPEN = "OPEN"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    FULLY_MATCHED = "FULLY_MATCHED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class MatchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
