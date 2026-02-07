import {
  useMyMatches,
  useAcceptMatch,
  useRejectMatch,
  useCancelMatch,
  useMatchContact,
} from "../hooks/useMatches";
import { useAuth } from "../hooks/useAuth";
import StatusBadge from "../components/StatusBadge";
import RoomBadge from "../components/RoomBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { MatchStatus, ListingType } from "../types";
import type { MatchResponse } from "../types";
import { useState } from "react";

function WhatsAppButton({ matchId }: { matchId: string }) {
  const { data: contact, isLoading } = useMatchContact(matchId, true);

  if (isLoading) return <span className="text-xs text-gray-400">Loading contact...</span>;
  if (!contact?.phone) return null;

  const phone = contact.phone.replace(/[^0-9+]/g, "");
  const whatsappUrl = `https://wa.me/${phone.startsWith("+") ? phone.slice(1) : phone}`;

  return (
    <a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 rounded-lg bg-green-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-600 transition"
    >
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
      </svg>
      Chat with {contact.name}
    </a>
  );
}

export default function MatchesPage() {
  const { user } = useAuth();
  const { data: matches, isLoading } = useMyMatches();
  const acceptMatch = useAcceptMatch();
  const rejectMatch = useRejectMatch();
  const cancelMatch = useCancelMatch();
  const [error, setError] = useState("");

  if (isLoading) return <LoadingSpinner />;

  // Deduplicate swap legs: for paired swaps, both matches reference each other.
  // Keep only one per pair so each swap shows once.
  const deduplicated = (() => {
    if (!matches) return [];
    const ids = new Set(matches.map((m) => m.id));
    return matches.filter((m) => {
      if (!m.paired_match_id) return true;
      // If paired match isn't in our results, keep this one
      if (!ids.has(m.paired_match_id)) return true;
      // Both exist: keep the one with smaller ID (deterministic)
      return m.id < m.paired_match_id;
    });
  })();

  const incoming = deduplicated.filter((m) => m.claimant_uid !== user?.uid);
  const outgoing = deduplicated.filter((m) => m.claimant_uid === user?.uid);

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

  const handleCancel = async (id: string) => {
    setError("");
    try {
      await cancelMatch.mutateAsync(id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel bid");
    }
  };

  const MatchRow = ({ match }: { match: MatchResponse }) => {
    const isProposed = match.status === MatchStatus.PROPOSED;
    const isAccepted = match.status === MatchStatus.ACCEPTED;
    const isIncoming = match.claimant_uid !== user?.uid;

    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
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
            <div className="flex gap-2 sm:flex-shrink-0">
              <button
                onClick={() => handleAccept(match.id)}
                disabled={acceptMatch.isPending}
                className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition"
              >
                Accept
              </button>
              <button
                onClick={() => handleReject(match.id)}
                disabled={rejectMatch.isPending}
                className="rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
              >
                Reject
              </button>
            </div>
          )}
          {isProposed && !isIncoming && (
            <button
              onClick={() => handleCancel(match.id)}
              disabled={cancelMatch.isPending}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition"
            >
              {cancelMatch.isPending ? "Cancelling..." : "Cancel Bid"}
            </button>
          )}
        </div>
        {isIncoming && match.message && (
          <div className="mt-3 border-t border-gray-100 pt-3">
            <p className="text-xs font-medium text-gray-500">Message from bidder</p>
            <p className="mt-1 text-sm text-gray-700">{match.message}</p>
          </div>
        )}
        {isAccepted && (
          <div className="mt-3 border-t border-gray-100 pt-3">
            <p className="mb-2 text-xs font-medium text-gray-500">
              Continue the deal on WhatsApp
            </p>
            <WhatsAppButton matchId={match.id} />
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

      {!deduplicated.length ? (
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
