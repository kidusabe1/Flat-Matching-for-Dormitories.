import secrets
from datetime import datetime, timezone, timedelta

from google.cloud.firestore_v1 import AsyncClient

from app.config import get_settings
from app.middleware.error_handler import ConflictError, NotFoundError
from app.services.email_service import send_verification_email

COLLECTION = "email_verifications"


async def send_pin(db: AsyncClient, uid: str, email: str) -> None:
    """Generate a 6-digit PIN, store it, and email it to the user.

    If a valid (unexpired, unverified) PIN already exists, resend it
    instead of generating a new one.
    """
    settings = get_settings()

    # Reuse existing PIN if still valid
    doc = await db.collection(COLLECTION).document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        if (
            not data.get("verified")
            and datetime.now(timezone.utc) < data["expires_at"]
        ):
            await send_verification_email(email, data["pin"])
            return

    pin = "".join(secrets.choice("0123456789") for _ in range(6))
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.verification_pin_expiry_minutes
    )

    await db.collection(COLLECTION).document(uid).set(
        {
            "email": email,
            "pin": pin,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "verified": False,
        }
    )

    await send_verification_email(email, pin)


async def verify_pin(db: AsyncClient, uid: str, pin: str) -> None:
    """Verify the PIN the user submitted."""
    doc = await db.collection(COLLECTION).document(uid).get()
    if not doc.exists:
        raise NotFoundError("No verification PIN found. Please request a new one.")

    data = doc.to_dict()

    if data.get("verified"):
        raise ConflictError("Email is already verified.")

    if datetime.now(timezone.utc) > data["expires_at"]:
        raise ConflictError("PIN has expired. Please request a new one.")

    if data["pin"] != pin:
        raise ConflictError("Incorrect PIN. Please try again.")

    await db.collection(COLLECTION).document(uid).update({"verified": True})


async def is_verified(db: AsyncClient, uid: str) -> bool:
    """Check whether the user's email has been verified."""
    doc = await db.collection(COLLECTION).document(uid).get()
    if not doc.exists:
        return False
    return doc.to_dict().get("verified", False)
