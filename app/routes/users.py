from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.models.user import (
    UserProfile,
    UserProfileCreate,
    UserProfilePublic,
    UserProfileUpdate,
)
from app.services.firestore_client import get_db
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/profile", response_model=UserProfile, status_code=201)
async def create_profile(
    data: UserProfileCreate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await user_service.create_user(db, user.uid, user.email, data)


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await user_service.get_user(db, user.uid)


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    data: UserProfileUpdate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await user_service.update_user(db, user.uid, data)


@router.get("/{uid}", response_model=UserProfilePublic)
async def get_user_profile(
    uid: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await user_service.get_user_public(db, uid)
