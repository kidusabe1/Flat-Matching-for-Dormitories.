import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth, credentials

from app.auth.models import FirebaseUser
from app.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)
_initialized = False


def _ensure_firebase_initialized() -> None:
    global _initialized
    if _initialized:
        return
    if firebase_admin._apps:
        _initialized = True
        return
    settings = get_settings()
    if settings.google_application_credentials:
        cred = credentials.Certificate(settings.google_application_credentials)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
    _initialized = True


async def get_current_user(
    credential: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> FirebaseUser:
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _ensure_firebase_initialized()
    try:
        decoded_token = firebase_auth.verify_id_token(credential.credentials)
        return FirebaseUser(
            uid=decoded_token["uid"],
            email=decoded_token.get("email", ""),
            name=decoded_token.get("name", ""),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
