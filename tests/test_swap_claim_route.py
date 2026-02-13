"""Tests for swap claim route — POST /listings/{id}/claim with claimant_listing_id."""

import pytest

from tests.conftest import _make_doc_snapshot, make_listing_data


class TestClaimSwap:
    @pytest.mark.asyncio
    async def test_claim_swap_success(self, client, mock_db):
        """User B claims User A's swap listing with their own swap listing."""
        # User A's swap listing (wants ILANOT_STUDIO, has PARK_SHARED_2BR)
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="owner-uid",
            room_id="room-A",
            room_category="PARK_SHARED_2BR",
            room_building="Building 3",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", target)

        # User B's swap listing (wants PARK_SHARED_2BR, has ILANOT_STUDIO)
        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_id="room-B",
            room_category="ILANOT_STUDIO",
            room_building="Building 5",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_claim_swap_own_listing_fails(self, client, mock_db):
        """Cannot claim your own listing."""
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_category="PARK_SHARED_2BR",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", target)

        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_category="ILANOT_STUDIO",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_claim_swap_non_swap_listing_fails(self, client, mock_db):
        """Cannot swap-claim a LEASE_TRANSFER listing."""
        target = make_listing_data(
            listing_type="LEASE_TRANSFER",
            status="OPEN",
            owner_uid="owner-uid",
        )
        mock_db.register_doc("listings", "listing-A", target)

        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_category="ILANOT_STUDIO",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_claim_swap_incompatible_categories_fails(self, client, mock_db):
        """Swap claim fails when categories are not mutually desired."""
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="owner-uid",
            room_category="PARK_SHARED_2BR",
            desired_categories=["ILANOT_PRIVATE"],  # wants PRIVATE, not STUDIO
        )
        mock_db.register_doc("listings", "listing-A", target)

        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_category="ILANOT_STUDIO",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_claim_swap_listing_not_open_fails(self, client, mock_db):
        """Cannot claim a completed swap listing."""
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="COMPLETED",
            owner_uid="owner-uid",
            room_category="PARK_SHARED_2BR",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", target)

        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="test-uid-123",
            room_category="ILANOT_STUDIO",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_claim_swap_claimant_not_owner_fails(self, client, mock_db):
        """Cannot use someone else's listing as your claimant listing."""
        target = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="owner-uid",
            room_category="PARK_SHARED_2BR",
            desired_categories=["ILANOT_STUDIO"],
        )
        mock_db.register_doc("listings", "listing-A", target)

        claimant = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="someone-else",  # Not test-uid-123
            room_category="ILANOT_STUDIO",
            desired_categories=["PARK_SHARED_2BR"],
        )
        mock_db.register_doc("listings", "listing-B", claimant)

        resp = await client.post("/api/v1/listings/listing-A/claim", json={
            "claimant_listing_id": "listing-B",
        })
        assert resp.status_code == 403
