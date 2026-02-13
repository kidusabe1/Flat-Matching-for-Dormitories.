"""Integration test: Full swap lifecycle through HTTP routes."""

import pytest

from tests.conftest import (
    make_listing_data,
    make_match_data,
    make_room_data,
    make_transaction_data,
)


class TestSwapLifecycle:
    """End-to-end swap flow: two users create swap requests → claim → accept → confirm."""

    @pytest.mark.asyncio
    async def test_create_swap_request_a(self, client, mock_db):
        """User A creates a swap request (has PARK_SHARED_2BR, wants ILANOT_STUDIO)."""
        mock_db.register_doc("rooms", "room-A", make_room_data(
            category="PARK_SHARED_2BR", occupant_uid="test-uid-123",
        ))
        mock_db.register_collection_docs("listings", [])

        resp = await client.post("/api/v1/listings/swap-request", json={
            "room_id": "room-A",
            "lease_start_date": "2026-03-01",
            "lease_end_date": "2026-08-31",
            "description": "Want to swap to studio",
            "desired_categories": ["ILANOT_STUDIO"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["listing_type"] == "SWAP_REQUEST"
        assert data["status"] == "OPEN"
        assert "ILANOT_STUDIO" in data["desired_categories"]

    @pytest.mark.asyncio
    async def test_swap_claim_creates_paired_matches(self, client, mock_db):
        """User A claims User B's swap listing → 2 paired matches created."""
        # User B's listing (has ILANOT_STUDIO, wants PARK_SHARED_2BR)
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-B",
            room_id="room-B",
            room_category="ILANOT_STUDIO",
            room_building="Building 5",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", target)

        # User A's listing (has PARK_SHARED_2BR, wants ILANOT_STUDIO)
        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_id="room-A",
            room_category="PARK_SHARED_2BR",
            room_building="Building 3",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", claimant)

        resp = await client.post("/api/v1/listings/listing-B/claim", json={
            "claimant_listing_id": "listing-A",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "match_1" in data
        assert "match_2" in data

    @pytest.mark.asyncio
    async def test_accept_swap_match(self, client, mock_db):
        """Owner accepts a swap match → listing → PENDING_APPROVAL."""
        listing = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", listing)

        match = make_match_data(
            match_type="SWAP_LEG",
            status="PROPOSED",
            listing_id="listing-A",
            claimant_uid="user-B",
            claimant_listing_id="listing-B",
            paired_match_id="match-2",
        )
        mock_db.register_doc("matches", "match-1", match)

        # Paired match
        paired = make_match_data(
            match_type="SWAP_LEG",
            status="PROPOSED",
            listing_id="listing-B",
            claimant_uid="user-B",
            paired_match_id="match-1",
        )
        mock_db.register_doc("matches", "match-2", paired)

        # Listing B for paired match
        listing_b = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-B",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", listing_b)

        # Other bids stream
        mock_db.register_collection_docs("matches", [])

        resp = await client.post("/api/v1/matches/match-1/accept")
        assert resp.status_code == 200
