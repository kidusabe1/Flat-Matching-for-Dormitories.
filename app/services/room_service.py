from datetime import datetime, timezone

from google.cloud.firestore_v1 import AsyncClient

from app.middleware.error_handler import ForbiddenError, NotFoundError
from app.models.room import Room, RoomCreate, RoomUpdate


async def _assert_admin(db: AsyncClient, uid: str) -> None:
    """Raise ForbiddenError unless the user has the admin role."""
    user_doc = await db.collection("users").document(uid).get()
    if not user_doc.exists or user_doc.to_dict().get("role") != "admin":
        raise ForbiddenError("Only administrators can manage rooms")


async def create_room(db: AsyncClient, data: RoomCreate, requester_uid: str) -> Room:
    await _assert_admin(db, requester_uid)
    now = datetime.now(timezone.utc)
    doc_data = {
        "building": data.building,
        "floor": data.floor,
        "room_number": data.room_number,
        "category": data.category.value,
        "description": data.description,
        "amenities": data.amenities,
        "occupant_uid": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    _, doc_ref = await db.collection("rooms").add(doc_data)
    return Room(id=doc_ref.id, **doc_data)


async def get_room(db: AsyncClient, room_id: str) -> Room:
    doc = await db.collection("rooms").document(room_id).get()
    if not doc.exists:
        raise NotFoundError(f"Room {room_id} not found")
    data = doc.to_dict()
    return Room(id=doc.id, **data)


async def list_rooms(
    db: AsyncClient,
    category: str | None = None,
    building: str | None = None,
) -> list[Room]:
    query = db.collection("rooms").where("is_active", "==", True)
    if category:
        query = query.where("category", "==", category)
    if building:
        query = query.where("building", "==", building)

    rooms = []
    async for doc in query.stream():
        data = doc.to_dict()
        rooms.append(Room(id=doc.id, **data))
    return rooms


async def update_room(
    db: AsyncClient, room_id: str, data: RoomUpdate, requester_uid: str
) -> Room:
    await _assert_admin(db, requester_uid)
    doc_ref = db.collection("rooms").document(room_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise NotFoundError(f"Room {room_id} not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    await doc_ref.update(updates)

    updated_doc = await doc_ref.get()
    return Room(id=updated_doc.id, **updated_doc.to_dict())
