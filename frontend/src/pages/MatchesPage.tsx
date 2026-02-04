import { useMyMatches, useAcceptMatch, useRejectMatch } from "../hooks/useMatches";
import { useAuth } from "../hooks/useAuth";
import StatusBadge from "../components/StatusBadge";
import RoomBadge from "../components/RoomBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { MatchStatus, ListingType } from "../types";
import type { MatchResponse } from "../types";
import { useState } from "react";

export default function MatchesPage() {
  const { user } = useAuth();
  const { data: matches, isLoading } = useMyMatches();
  const acceptMatch = useAcceptMatch();
  const rejectMatch = useRejectMatch();
  const [error, setError] = useState("");

  if (isLoading) return <LoadingSpinner />;

  const incoming =
    matches?.filter((m) => m.claimant_uid !== user?.uid) ?? [];
  const outgoing =
    matches?.filter((m) => m.claimant_uid === user?.uid) ?? [];

  const handleAccept = async (id: string) => {
    setError("");
    try {
      await acceptMatch.mutateAsync(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to accept match");
    }
  };

  const handleReject = async (id: string) => {
    setError("");
    try {
      await rejectMatch.mutateAsync(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reject match");
    }
  };

  const MatchRow = ({ match }: { match: MatchResponse }) => {
    const isProposed = match.status === MatchStatus.PROPOSED;
    const isIncoming = match.claimant_uid !== user?.uid;

    return (
      <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <div className="flex items-center gap-2">
            <RoomBadge category={match.offered_room_category} />
            <span className="text-sm font-medium text-gray-900">
              {match.offered_room_building}
            </span>
            <StatusBadge status={match.status} />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            {match.match_type === ListingType.LEASE_TRANSFER
              ? "Lease Transfer"
              : "Swap Request"}
            {" — "}
            {match.proposed_at
              ? new Date(match.proposed_at).toLocaleDateString()
              : ""}
          </p>
        </div>
        {isProposed && isIncoming && (
          <div className="flex gap-2">
            <button
              onClick={() => handleAccept(match.id)}
              disabled={acceptMatch.isPending}
              className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition"
            >
              Accept
            </button>
            <button
              onClick={() => handleReject(match.id)}
              disabled={rejectMatch.isPending}
              className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
            >
              Reject
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <h1 className="mb-6 text-xl font-bold text-gray-900">Matches</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!matches?.length ? (
        <EmptyState
          title="No matches yet"
          description="Matches will appear here when someone claims your listing or you claim theirs"
        />
      ) : (
        <div className="space-y-8">
          {/* Incoming */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-gray-700">
              Incoming ({incoming.length})
            </h2>
            {incoming.length === 0 ? (
              <p className="text-sm text-gray-400">No incoming matches</p>
            ) : (
              <div className="space-y-3">
                {incoming.map((match) => (
                  <MatchRow key={match.id} match={match} />
                ))}
              </div>
            )}
          </section>

          {/* Outgoing */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-gray-700">
              Outgoing ({outgoing.length})
            </h2>
            {outgoing.length === 0 ? (
              <p className="text-sm text-gray-400">No outgoing matches</p>
            ) : (
              <div className="space-y-3">
                {outgoing.map((match) => (
                  <MatchRow key={match.id} match={match} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
