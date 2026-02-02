"""Tests for matching engine logic."""

from datetime import date, datetime, timezone

import pytest

from app.services.matching_engine import _dates_overlap, find_compatible_swaps
from tests.conftest import _make_doc_snapshot, make_listing_data


# ──────────────────────────────────────────────────────────
# Date Overlap Tests
# ──────────────────────────────────────────────────────────

class TestDatesOverlap:
    def test_identical_ranges(self):
        assert _dates_overlap(
            date(2026, 3, 1), date(2026, 8, 31),
            date(2026, 3, 1), date(2026, 8, 31),
        ) is True

    def test_overlapping_ranges(self):
        assert _dates_overlap(
            date(2026, 3, 1), date(2026, 8, 31),
            date(2026, 6, 1), date(2026, 12, 31),
        ) is True

    def test_one_day_overlap(self):
        assert _dates_overlap(
            date(2026, 3, 1), date(2026, 6, 1),
            date(2026, 6, 1), date(2026, 9, 1),
        ) is True

    def test_no_overlap(self):
        assert _dates_overlap(
            date(2026, 3, 1), date(2026, 5, 31),
            date(2026, 6, 1), date(2026, 8, 31),
        ) is False

    def test_b_before_a(self):
        assert _dates_overlap(
            date(2026, 6, 1), date(2026, 8, 31),
            date(2026, 3, 1), date(2026, 5, 31),
        ) is False

    def test_contained_range(self):
        assert _dates_overlap(
            date(2026, 3, 1), date(2026, 12, 31),
            date(2026, 6, 1), date(2026, 8, 31),
        ) is True

    def test_datetime_inputs(self):
        assert _dates_overlap(
            datetime(2026, 3, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 31, tzinfo=timezone.utc),
            datetime(2026, 6, 1, tzinfo=timezone.utc),
            datetime(2026, 12, 31, tzinfo=timezone.utc),
        ) is True

    def test_mixed_date_datetime(self):
        assert _dates_overlap(
            date(2026, 3, 1),
            datetime(2026, 8, 31, tzinfo=timezone.utc),
            datetime(2026, 6, 1, tzinfo=timezone.utc),
            date(2026, 12, 31),
        ) is True

    def test_adjacent_ranges_no_overlap(self):
        assert _dates_overlap(
            date(2026, 1, 1), date(2026, 1, 31),
            date(2026, 2, 1), date(2026, 2, 28),
        ) is False

    def test_same_day_range(self):
        assert _dates_overlap(
            date(2026, 5, 15), date(2026, 5, 15),
            date(2026, 5, 15), date(2026, 5, 15),
        ) is True


# ──────────────────────────────────────────────────────────
# Swap Compatibility Tests
# ──────────────────────────────────────────────────────────

class TestFindCompatibleSwaps:
    @pytest.mark.asyncio
    async def test_finds_compatible_swap(self, mock_db):
        """Two swap listings wanting each other's category should match."""
        # Source listing: category A, wants B
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            desired_categories=["B"],
        )
        mock_db.register_doc("listings", "listing-source", source)

        # Candidate: category B, wants A
        candidate = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-b",
            room_category="B",
            room_building="Building 3",
            desired_categories=["A"],
        )
        candidate_snap = _make_doc_snapshot("listing-candidate", candidate)
        mock_db.register_collection_docs("listings", [candidate_snap])

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert len(results) == 1
        assert results[0]["id"] == "listing-candidate"

    @pytest.mark.asyncio
    async def test_excludes_own_listing(self, mock_db):
        """Should not match against the user's own listing."""
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            desired_categories=["B"],
        )
        mock_db.register_doc("listings", "listing-source", source)

        # Candidate owned by same user
        candidate = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-a",
            room_category="B",
            desired_categories=["A"],
        )
        candidate_snap = _make_doc_snapshot("listing-other", candidate)
        mock_db.register_collection_docs("listings", [candidate_snap])

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_excludes_non_matching_category(self, mock_db):
        """Candidate that doesn't want the source's category should not match."""
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            desired_categories=["B"],
        )
        mock_db.register_doc("listings", "listing-source", source)

        # Candidate wants C, not A
        candidate = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-b",
            room_category="B",
            desired_categories=["C"],
        )
        candidate_snap = _make_doc_snapshot("listing-candidate", candidate)
        mock_db.register_collection_docs("listings", [candidate_snap])

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_excludes_non_overlapping_dates(self, mock_db):
        """Listings with non-overlapping dates should not match."""
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            desired_categories=["B"],
            lease_start_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            lease_end_date=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
        mock_db.register_doc("listings", "listing-source", source)

        # No date overlap
        candidate = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-b",
            room_category="B",
            desired_categories=["A"],
            lease_start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            lease_end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )
        candidate_snap = _make_doc_snapshot("listing-candidate", candidate)
        mock_db.register_collection_docs("listings", [candidate_snap])

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_respects_building_preference(self, mock_db):
        """Building preference filter should exclude non-matching buildings."""
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            room_building="Building 3",
            desired_categories=["B"],
            desired_buildings=["Building 5"],
        )
        mock_db.register_doc("listings", "listing-source", source)

        # Candidate in Building 3, not Building 5
        candidate = make_listing_data(
            listing_type="SWAP_REQUEST",
            status="OPEN",
            owner_uid="user-b",
            room_category="B",
            room_building="Building 3",
            desired_categories=["A"],
        )
        candidate_snap = _make_doc_snapshot("listing-candidate", candidate)
        mock_db.register_collection_docs("listings", [candidate_snap])

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_nonexistent_listing_returns_empty(self, mock_db):
        """Querying compatibility for a nonexistent listing returns empty."""
        results = await find_compatible_swaps(mock_db, "nonexistent-listing")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_desired_categories_returns_empty(self, mock_db):
        """Listing with no desired categories returns empty."""
        source = make_listing_data(
            listing_type="SWAP_REQUEST",
            owner_uid="user-a",
            room_category="A",
            desired_categories=[],
        )
        mock_db.register_doc("listings", "listing-source", source)

        results = await find_compatible_swaps(mock_db, "listing-source")
        assert results == []
