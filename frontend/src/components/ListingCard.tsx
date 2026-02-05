import { Link } from "react-router-dom";
import type { ListingResponse } from "../types";
import { ListingType } from "../types";
import StatusBadge from "./StatusBadge";
import RoomBadge from "./RoomBadge";

interface ListingCardProps {
  listing: ListingResponse;
}

export default function ListingCard({ listing }: ListingCardProps) {
  return (
    <Link
      to={`/listings/${listing.id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <RoomBadge category={listing.room_category} />
          <span className="text-sm text-gray-500">
            {listing.listing_type === ListingType.LEASE_TRANSFER
              ? "Lease Transfer"
              : "Swap Request"}
          </span>
        </div>
        <StatusBadge status={listing.status} />
      </div>

      <div className="mt-3">
        <p className="font-medium text-gray-900">
          {listing.room_building} — Room {listing.room_category}
        </p>
        <p className="mt-1 text-sm text-gray-500 line-clamp-2">
          {listing.description || "No description provided"}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
        <span>
          {new Date(listing.lease_start_date).toLocaleDateString()} —{" "}
          {new Date(listing.lease_end_date).toLocaleDateString()}
        </span>
        {listing.move_in_date && (
          <span>
            Move-in: {new Date(listing.move_in_date).toLocaleDateString()}
          </span>
        )}
        {listing.asking_price != null && (
          <span className="font-medium text-gray-700">
            ₪{listing.asking_price}
          </span>
        )}
      </div>
    </Link>
  );
}
