from datetime import datetime

from pydantic import BaseModel


class MatchResponse(BaseModel):
    id: str
    match_type: str
    status: str
    listing_id: str
    claimant_uid: str
    claimant_listing_id: str | None = None
    offered_room_id: str
    offered_room_category: str
    offered_room_building: str
    proposed_at: datetime | None = None
    responded_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
