from datetime import date, datetime

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: str
    transaction_type: str
    status: str
    match_id: str | None = None
    match_ids: list[str] | None = None
    from_uid: str | None = None
    to_uid: str | None = None
    room_id: str | None = None
    party_a_uid: str | None = None
    party_a_room_id: str | None = None
    party_b_uid: str | None = None
    party_b_room_id: str | None = None
    lease_start_date: date | None = None
    lease_end_date: date | None = None
    initiated_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
