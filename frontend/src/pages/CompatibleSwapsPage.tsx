import { useParams, useNavigate } from "react-router-dom";
import {
  useCompatibleSwaps,
  useListing,
  useClaimListing,
} from "../hooks/useListings";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import RoomBadge from "../components/RoomBadge";
import { useState } from "react";

export default function CompatibleSwapsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: listing } = useListing(id);
  const { data: compatible, isLoading } = useCompatibleSwaps(id);
  const claimListing = useClaimListing();
  const [claimingId, setClaimingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleOfferSwap = async (claimantListingId: string) => {
    if (!id) return;
    setClaimingId(claimantListingId);
    setError("");
    try {
      await claimListing.mutateAsync({
        id,
        claim: { claimant_listing_id: claimantListingId },
      });
      navigate("/matches");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to offer swap");
      setClaimingId(null);
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="mx-auto max-w-2xl">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-sm text-blue-600 hover:text-blue-700"
      >
        &larr; Back to listing
      </button>

      <h1 className="mb-2 text-xl font-bold text-gray-900">
        Compatible Swaps
      </h1>
      {listing && (
        <p className="mb-6 text-sm text-gray-500">
          Showing compatible swap partners for your listing in{" "}
          {listing.room_building}
        </p>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!compatible?.length ? (
        <EmptyState
          title="No compatible swaps found"
          description="No one is currently looking to swap for a room matching your criteria"
        />
      ) : (
        <div className="space-y-3">
          {compatible.map((swap) => (
            <div
              key={swap.id}
              className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4"
            >
              <div>
                <div className="flex items-center gap-2">
                  <RoomBadge category={swap.room_category} />
                  <span className="text-sm font-medium text-gray-900">
                    {swap.room_building}
                  </span>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {new Date(swap.lease_start_date).toLocaleDateString()} —{" "}
                  {new Date(swap.lease_end_date).toLocaleDateString()}
                </p>
                {swap.description && (
                  <p className="mt-1 text-sm text-gray-600 line-clamp-1">
                    {swap.description}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleOfferSwap(swap.id)}
                disabled={claimingId === swap.id}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {claimingId === swap.id ? "Offering..." : "Offer Swap"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
