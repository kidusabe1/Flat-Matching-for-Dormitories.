import { useState } from "react";
import { useListings } from "../hooks/useListings";
import ListingCard from "../components/ListingCard";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { ListingType, RoomCategory } from "../types";
import { Link } from "react-router-dom";

export default function BrowseListingsPage() {
  const [listingType, setListingType] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [building, setBuilding] = useState("");
  const [page, setPage] = useState(1);
  const limit = 12;

  const { data, isLoading } = useListings({
    listing_type: listingType || undefined,
    category: category || undefined,
    building: building || undefined,
    page,
    limit,
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Browse Listings</h1>
        <Link
          to="/listings/new"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
        >
          New Listing
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <select
          value={listingType}
          onChange={(e) => {
            setListingType(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        >
          <option value="">All Types</option>
          <option value={ListingType.LEASE_TRANSFER}>Lease Transfer</option>
          <option value={ListingType.SWAP_REQUEST}>Swap Request</option>
        </select>

        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        >
          <option value="">All Categories</option>
          <optgroup label="Park 100 Complex">
            <option value={RoomCategory.PARK_SHARED_2BR}>Shared 2BR</option>
            <option value={RoomCategory.PARK_SHARED_3BR}>Shared 3BR</option>
            <option value={RoomCategory.PARK_STUDIO}>Studio</option>
            <option value={RoomCategory.PARK_COUPLES}>Couples</option>
          </optgroup>
          <optgroup label="Ilanot Complex">
            <option value={RoomCategory.ILANOT_SHARED_1BR}>Shared 1BR</option>
            <option value={RoomCategory.ILANOT_SHARED_2BR}>Shared 2BR</option>
            <option value={RoomCategory.ILANOT_PRIVATE}>Private Room</option>
            <option value={RoomCategory.ILANOT_SHARED_LARGE}>Shared Large</option>
            <option value={RoomCategory.ILANOT_STUDIO}>Studio</option>
            <option value={RoomCategory.ILANOT_COUPLES}>Couples</option>
          </optgroup>
        </select>

        <input
          type="text"
          placeholder="Building..."
          value={building}
          onChange={(e) => {
            setBuilding(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        />
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : !data?.items.length ? (
        <EmptyState
          title="No listings found"
          description="Try adjusting your filters or create a new listing"
          action={
            <Link
              to="/listings/new"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Create Listing
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>

          {/* Pagination */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {(page - 1) * limit + 1}–
              {Math.min(page * limit, data.total)} of {data.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.has_next}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
