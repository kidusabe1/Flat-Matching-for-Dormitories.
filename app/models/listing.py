from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import RoomCategory


class LeaseTransferCreate(BaseModel):
    room_id: str
    lease_start_date: date
    lease_end_date: date
    description: str = ""
    asking_price: int | None = None


class SwapRequestCreate(BaseModel):
    room_id: str
    lease_start_date: date
    lease_end_date: date
    description: str = ""
    desired_categories: list[RoomCategory]
    desired_buildings: list[str] | None = None
    desired_min_start: date | None = None
    desired_max_end: date | None = None


class ListingUpdate(BaseModel):
    description: str | None = None
    asking_price: int | None = None
    lease_start_date: date | None = None
    lease_end_date: date | None = None
    desired_categories: list[RoomCategory] | None = None
    desired_buildings: list[str] | None = None


class ClaimRequest(BaseModel):
    message: str | None = None
    claimant_listing_id: str | None = None


class ListingResponse(BaseModel):
    id: str
    listing_type: str
    status: str
    owner_uid: str
    room_id: str
    room_category: str
    room_building: str
    lease_start_date: date
    lease_end_date: date
    description: str
    asking_price: int | None = None
    desired_categories: list[str] | None = None
    desired_buildings: list[str] | None = None
    desired_min_start: date | None = None
    desired_max_end: date | None = None
    replacement_match_id: str | None = None
    target_match_id: str | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedListings(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    limit: int
    has_next: bool
