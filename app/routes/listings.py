from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1 import AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.models import FirebaseUser
from app.models.listing import (
    ClaimRequest,
    LeaseTransferCreate,
    ListingResponse,
    ListingUpdate,
    PaginatedListings,
    SwapRequestCreate,
)
from app.models.match import MatchResponse
from app.services import listing_service, matching_engine
from app.services.firestore_client import get_db

router = APIRouter(prefix="/api/v1/listings", tags=["listings"])


@router.post("/lease-transfer", response_model=ListingResponse, status_code=201)
async def create_lease_transfer(
    data: LeaseTransferCreate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.create_lease_transfer(db, user.uid, data)


@router.post("/swap-request", response_model=ListingResponse, status_code=201)
async def create_swap_request(
    data: SwapRequestCreate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.create_swap_request(db, user.uid, data)


@router.get("/my", response_model=list[ListingResponse])
async def get_my_listings(
    status: str | None = Query(None),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.get_user_listings(db, user.uid, status=status)


@router.get("", response_model=PaginatedListings)
async def browse_listings(
    listing_type: str | None = Query(None, alias="type"),
    category: str | None = Query(None),
    status: str | None = Query(None),
    building: str | None = Query(None),
    limit: int = Query(20, le=100),
    page: int = Query(1, ge=1),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.list_listings(
        db,
        listing_type=listing_type,
        category=category,
        status=status,
        building=building,
        limit=limit,
        page=page,
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.get_listing(db, listing_id)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    data: ListingUpdate,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.update_listing(db, listing_id, user.uid, data)


@router.post("/{listing_id}/cancel", response_model=ListingResponse)
async def cancel_listing(
    listing_id: str,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    return await listing_service.cancel_listing(db, listing_id, user.uid)


@router.post("/{listing_id}/claim")
async def claim_listing(
    listing_id: str,
    data: ClaimRequest,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    if data.claimant_listing_id:
        result = await listing_service.claim_swap(
            db, listing_id, user.uid, data.claimant_listing_id
        )
    else:
        result = await listing_service.claim_listing(
            db, listing_id, user.uid, data.message
        )
    return result


@router.get("/{listing_id}/compatible", response_model=list[ListingResponse])
async def find_compatible(
    listing_id: str,
    limit: int = Query(20, le=100),
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_db),
):
    results = await matching_engine.find_compatible_swaps(db, listing_id, limit=limit)
    return [listing_service._to_listing_response(r["id"], r) for r in results]
