from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1 import AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.models.transaction import TransactionResponse
from app.services import transaction_service
from app.services.firestore_client import get_db

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("/my", response_model=list[TransactionResponse])
async def get_my_transactions(
    status: str | None = Query(None),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await transaction_service.get_user_transactions(
        db, user.uid, status=status
    )


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(
    tx_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await transaction_service.get_transaction(db, tx_id, user.uid)


@router.post("/{tx_id}/confirm", response_model=TransactionResponse)
async def confirm_transaction(
    tx_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await transaction_service.confirm_transaction(db, tx_id, user.uid)


@router.post("/{tx_id}/cancel", response_model=TransactionResponse)
async def cancel_transaction(
    tx_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await transaction_service.cancel_transaction(db, tx_id, user.uid)
