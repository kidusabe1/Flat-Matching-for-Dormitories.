from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me")
async def get_my_profile(user: FirebaseUser = Depends(get_current_user)):
    return {"uid": user.uid, "email": user.email, "name": user.name}
