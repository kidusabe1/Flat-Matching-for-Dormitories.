import { Link } from "react-router-dom";
import { useMyListings } from "../hooks/useListings";
import ListingCard from "../components/ListingCard";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

export default function MyListingsPage() {
  const { data: listings, isLoading } = useMyListings();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">My Listings</h1>
        <Link
          to="/listings/new"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
        >
          New Listing
        </Link>
      </div>

      {!listings?.length ? (
        <EmptyState
          title="No listings yet"
          description="Create your first listing to get started"
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}
