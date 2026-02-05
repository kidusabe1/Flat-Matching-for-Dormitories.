from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import AsyncClient
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.services.firestore_client import get_db
from app.services import verification_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class PinRequest(BaseModel):
    pin: str


class VerificationStatus(BaseModel):
    verified: bool


class AuthStatus(BaseModel):
    verified: bool
    has_profile: bool


@router.post("/send-verification", response_model=VerificationStatus)
async def send_verification_pin(
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    """Generate and email a 6-digit verification PIN."""
    await verification_service.send_pin(db, user.uid, user.email)
    return VerificationStatus(verified=False)


@router.post("/verify-pin", response_model=VerificationStatus)
async def verify_pin(
    body: PinRequest,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    """Verify the PIN the user received by email."""
    await verification_service.verify_pin(db, user.uid, body.pin)
    return VerificationStatus(verified=True)


@router.get("/verification-status", response_model=VerificationStatus)
async def get_verification_status(
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    """Check whether the current user's email is verified."""
    verified = await verification_service.is_verified(db, user.uid)
    return VerificationStatus(verified=verified)


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    """Combined check: email verified + profile exists. Always returns 200."""
    verified = await verification_service.is_verified(db, user.uid)
    profile_doc = await db.collection("users").document(user.uid).get()
    return AuthStatus(verified=verified, has_profile=profile_doc.exists)
