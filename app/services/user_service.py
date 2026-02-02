from datetime import datetime, timezone

from google.cloud.firestore_v1 import AsyncClient

from app.middleware.error_handler import NotFoundError
from app.models.user import UserProfile, UserProfileCreate, UserProfileUpdate


async def create_user(
    db: AsyncClient, uid: str, email: str, data: UserProfileCreate
) -> UserProfile:
    now = datetime.now(timezone.utc)
    doc_data = {
        "uid": uid,
        "email": email,
        "full_name": data.full_name,
        "student_id": data.student_id,
        "phone": data.phone,
        "current_room_id": data.current_room_id,
        "created_at": now,
        "updated_at": now,
    }
    await db.collection("users").document(uid).set(doc_data)
    return UserProfile(**doc_data)


async def get_user(db: AsyncClient, uid: str) -> UserProfile:
    doc = await db.collection("users").document(uid).get()
    if not doc.exists:
        raise NotFoundError(f"User {uid} not found")
    return UserProfile(**doc.to_dict())


async def get_user_public(db: AsyncClient, uid: str) -> dict:
    doc = await db.collection("users").document(uid).get()
    if not doc.exists:
        raise NotFoundError(f"User {uid} not found")
    data = doc.to_dict()
    return {
        "uid": data["uid"],
        "full_name": data["full_name"],
        "current_room_id": data.get("current_room_id"),
    }


async def update_user(
    db: AsyncClient, uid: str, data: UserProfileUpdate
) -> UserProfile:
    doc_ref = db.collection("users").document(uid)
    doc = await doc_ref.get()
    if not doc.exists:
        raise NotFoundError(f"User {uid} not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    await doc_ref.update(updates)

    updated_doc = await doc_ref.get()
    return UserProfile(**updated_doc.to_dict())
