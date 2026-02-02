from datetime import datetime

from pydantic import BaseModel

from app.models.enums import RoomCategory


class RoomCreate(BaseModel):
    building: str
    floor: int
    room_number: str
    category: RoomCategory
    description: str = ""
    amenities: list[str] = []


class RoomUpdate(BaseModel):
    description: str | None = None
    amenities: list[str] | None = None
    is_active: bool | None = None


class Room(BaseModel):
    id: str
    building: str
    floor: int
    room_number: str
    category: RoomCategory
    description: str
    amenities: list[str]
    occupant_uid: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
