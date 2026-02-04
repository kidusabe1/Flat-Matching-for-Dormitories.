import { Link } from "react-router-dom";
import { useMyListings } from "../hooks/useListings";
import { useMyMatches } from "../hooks/useMatches";
import { useMyTransactions } from "../hooks/useTransactions";
import { useProfile } from "../hooks/useProfile";
import LoadingSpinner from "../components/LoadingSpinner";

export default function DashboardPage() {
  const profile = useProfile();
  const listings = useMyListings();
  const matches = useMyMatches();
  const transactions = useMyTransactions();

  if (profile.isLoading) return <LoadingSpinner />;

  const activeListings =
    listings.data?.filter(
      (l) =>
        l.status === "OPEN" ||
        l.status === "MATCHED" ||
        l.status === "PARTIAL_MATCH"
    ) ?? [];

  const pendingMatches =
    matches.data?.filter((m) => m.status === "PROPOSED") ?? [];

  const activeTransactions =
    transactions.data?.filter(
      (t) => t.status === "PENDING" || t.status === "IN_PROGRESS"
    ) ?? [];

  const cards = [
    {
      label: "Active Listings",
      count: activeListings.length,
      to: "/my-listings",
      color: "bg-blue-50 text-blue-700 border-blue-200",
    },
    {
      label: "Pending Matches",
      count: pendingMatches.length,
      to: "/matches",
      color: "bg-yellow-50 text-yellow-700 border-yellow-200",
    },
    {
      label: "Active Transactions",
      count: activeTransactions.length,
      to: "/transactions",
      color: "bg-green-50 text-green-700 border-green-200",
    },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">
          Welcome, {profile.data?.full_name ?? "User"}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Here's your dormitory exchange overview
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.label}
            to={card.to}
            className={`rounded-xl border p-5 transition hover:shadow-md ${card.color}`}
          >
            <p className="text-3xl font-bold">{card.count}</p>
            <p className="mt-1 text-sm font-medium">{card.label}</p>
          </Link>
        ))}
      </div>

      <div className="mt-8">
        <Link
          to="/listings/new"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4v16m8-8H4"
            />
          </svg>
          Create New Listing
        </Link>
      </div>
    </div>
  );
}
