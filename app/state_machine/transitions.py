from app.middleware.error_handler import InvalidTransitionError
from app.models.enums import LeaseTransferStatus, ListingType, SwapRequestStatus
from app.state_machine.listing_states import validate_lease_transfer_transition
from app.state_machine.swap_states import validate_swap_transition


def validate_transition(listing_type: str, current: str, target: str) -> bool:
    if listing_type == ListingType.LEASE_TRANSFER:
        return validate_lease_transfer_transition(
            LeaseTransferStatus(current), LeaseTransferStatus(target)
        )
    elif listing_type == ListingType.SWAP_REQUEST:
        return validate_swap_transition(
            SwapRequestStatus(current), SwapRequestStatus(target)
        )
    return False


def assert_transition(listing_type: str, current: str, target: str) -> None:
    if not validate_transition(listing_type, current, target):
        raise InvalidTransitionError(
            f"Cannot transition {listing_type} from {current} to {target}"
        )
