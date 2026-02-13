from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1 import AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.models.match import ContactResponse, MatchResponse
from app.services import match_service
from app.services.firestore_client import get_db

router = APIRouter(prefix="/api/v1/matches", tags=["matches"])


@router.get("/my", response_model=list[MatchResponse])
async def get_my_matches(
    status: str | None = Query(None),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.get_user_matches(db, user.uid, status=status)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.get_match(db, match_id, user.uid)


@router.post("/{match_id}/accept", response_model=MatchResponse)
async def accept_match(
    match_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.accept_match(db, match_id, user.uid)


@router.post("/{match_id}/reject", response_model=MatchResponse)
async def reject_match(
    match_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.reject_match(db, match_id, user.uid)


@router.post("/{match_id}/cancel", response_model=MatchResponse)
async def cancel_match(
    match_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.cancel_match(db, match_id, user.uid)


@router.get("/{match_id}/contact", response_model=ContactResponse)
async def get_match_contact(
    match_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await match_service.get_match_contact(db, match_id, user.uid)
