from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1 import AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.models.room import Room, RoomCreate, RoomUpdate
from app.services.firestore_client import get_db
from app.services import room_service

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.post("", response_model=Room, status_code=201)
async def create_room(
    data: RoomCreate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await room_service.create_room(db, data, user.uid)


@router.get("", response_model=list[Room])
async def list_rooms(
    category: str | None = Query(None),
    building: str | None = Query(None),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await room_service.list_rooms(db, category=category, building=building)


@router.get("/{room_id}", response_model=Room)
async def get_room(
    room_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await room_service.get_room(db, room_id)


@router.put("/{room_id}", response_model=Room)
async def update_room(
    room_id: str,
    data: RoomUpdate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await room_service.update_room(db, room_id, data, user.uid)
