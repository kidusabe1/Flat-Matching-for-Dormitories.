from datetime import datetime

from pydantic import BaseModel


class UserProfileCreate(BaseModel):
    full_name: str
    student_id: str
    phone: str
    current_room_id: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    current_room_id: str | None = None


class UserProfile(BaseModel):
    uid: str
    email: str
    full_name: str
    student_id: str
    phone: str
    current_room_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfilePublic(BaseModel):
    uid: str
    full_name: str
    current_room_id: str | None = None
