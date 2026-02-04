import { useParams, useNavigate, Link } from "react-router-dom";
import { useListing, useCancelListing, useClaimListing } from "../hooks/useListings";
import { useAuth } from "../hooks/useAuth";
import { ListingType } from "../types";
import StatusBadge from "../components/StatusBadge";
import RoomBadge from "../components/RoomBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import { useState } from "react";

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: listing, isLoading } = useListing(id);
  const cancelListing = useCancelListing();
  const claimListing = useClaimListing();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  if (isLoading) return <LoadingSpinner />;
  if (!listing) return <p className="text-gray-500">Listing not found</p>;

  const isOwner = listing.owner_uid === user?.uid;
  const isOpen = listing.status === "OPEN";

  const handleCancel = async () => {
    try {
      await cancelListing.mutateAsync(listing.id);
      navigate("/my-listings");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel");
    }
  };

  const handleClaim = async () => {
    try {
      await claimListing.mutateAsync({
        id: listing.id,
        claim: { message: message || undefined },
      });
      navigate("/matches");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to claim");
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-sm text-blue-600 hover:text-blue-700"
      >
        &larr; Back
      </button>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <RoomBadge category={listing.room_category} />
              <span className="text-sm text-gray-500">
                {listing.listing_type === ListingType.LEASE_TRANSFER
                  ? "Lease Transfer"
                  : "Swap Request"}
              </span>
            </div>
            <h1 className="mt-2 text-lg font-bold text-gray-900">
              {listing.room_building}
            </h1>
          </div>
          <StatusBadge status={listing.status} />
        </div>

        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium text-gray-500">Room ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{listing.room_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Lease Period</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(listing.lease_start_date).toLocaleDateString()} —{" "}
              {new Date(listing.lease_end_date).toLocaleDateString()}
            </dd>
          </div>
          {listing.move_in_date && (
            <div>
              <dt className="text-xs font-medium text-gray-500">
                {listing.listing_type === ListingType.LEASE_TRANSFER
                  ? "Transfer Date"
                  : "Move-in Date"}
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(listing.move_in_date).toLocaleDateString()}
              </dd>
            </div>
          )}
          {listing.asking_price != null && (
            <div>
              <dt className="text-xs font-medium text-gray-500">
                Asking Price
              </dt>
              <dd className="mt-1 text-sm font-medium text-gray-900">
                {listing.asking_price} NIS
              </dd>
            </div>
          )}
          {listing.desired_categories && listing.desired_categories.length > 0 && (
            <div>
              <dt className="text-xs font-medium text-gray-500">
                Desired Categories
              </dt>
              <dd className="mt-1 flex gap-1">
                {listing.desired_categories.map((cat) => (
                  <RoomBadge key={cat} category={cat} />
                ))}
              </dd>
            </div>
          )}
          {listing.desired_buildings && listing.desired_buildings.length > 0 && (
            <div>
              <dt className="text-xs font-medium text-gray-500">
                Desired Buildings
              </dt>
              <dd className="mt-1 text-sm text-gray-900">
                {listing.desired_buildings.join(", ")}
              </dd>
            </div>
          )}
        </dl>

        {listing.description && (
          <div className="mt-6">
            <h3 className="text-xs font-medium text-gray-500">Description</h3>
            <p className="mt-1 text-sm text-gray-700">{listing.description}</p>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="mt-6 flex flex-wrap gap-3">
          {isOwner && isOpen && (
            <button
              onClick={handleCancel}
              disabled={cancelListing.isPending}
              className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
            >
              {cancelListing.isPending ? "Cancelling..." : "Cancel Listing"}
            </button>
          )}

          {!isOwner &&
            isOpen &&
            listing.listing_type === ListingType.LEASE_TRANSFER && (
              <div className="flex w-full flex-col gap-3">
                <input
                  type="text"
                  placeholder="Optional message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                />
                <button
                  onClick={handleClaim}
                  disabled={claimListing.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
                >
                  {claimListing.isPending
                    ? "Claiming..."
                    : "Claim This Room"}
                </button>
              </div>
            )}

          {!isOwner &&
            isOpen &&
            listing.listing_type === ListingType.SWAP_REQUEST && (
              <Link
                to={`/listings/${listing.id}/compatible`}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
              >
                View Compatible Swaps
              </Link>
            )}
        </div>
      </div>
    </div>
  );
}
