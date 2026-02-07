import {
  useMyTransactions,
  useConfirmTransaction,
  useCancelTransaction,
} from "../hooks/useTransactions";
import { useMatchContact } from "../hooks/useMatches";
import StatusBadge from "../components/StatusBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { TransactionStatus, ListingType } from "../types";
import type { TransactionResponse } from "../types";
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

function TransactionCard({
  tx,
  onConfirm,
  onCancel,
  confirmPending,
  cancelPending,
}: {
  tx: TransactionResponse;
  onConfirm: (id: string) => void;
  onCancel: (id: string) => void;
  confirmPending: boolean;
  cancelPending: boolean;
}) {
  const isPending = tx.status === TransactionStatus.PENDING;
  const showWhatsApp =
    tx.status === TransactionStatus.PENDING ||
    tx.status === TransactionStatus.IN_PROGRESS ||
    tx.status === TransactionStatus.COMPLETED;
  const matchId = tx.match_id ?? tx.match_ids?.[0];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-900">
              {tx.transaction_type === ListingType.LEASE_TRANSFER
                ? "Lease Transfer"
                : "Room Swap"}
            </span>
            <StatusBadge status={tx.status} />
          </div>
          <div className="mt-2 text-xs text-gray-500 space-y-0.5">
            {tx.room_id && <p>Room: {tx.room_id}</p>}
            {tx.party_a_room_id && tx.party_b_room_id && (
              <p>
                Rooms: {tx.party_a_room_id} &harr; {tx.party_b_room_id}
              </p>
            )}
            {tx.initiated_at && (
              <p>
                Initiated:{" "}
                {new Date(tx.initiated_at).toLocaleDateString()}
              </p>
            )}
            {tx.completed_at && (
              <p>
                Completed:{" "}
                {new Date(tx.completed_at).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>
        {isPending && (
          <div className="flex gap-2 sm:flex-shrink-0">
            <button
              onClick={() => onConfirm(tx.id)}
              disabled={confirmPending}
              className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition"
            >
              Confirm
            </button>
            <button
              onClick={() => onCancel(tx.id)}
              disabled={cancelPending}
              className="rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
      {showWhatsApp && matchId && (
        <div className="mt-3 border-t border-gray-100 pt-3">
          <p className="mb-2 text-xs font-medium text-gray-500">
            Coordinate the exchange on WhatsApp
          </p>
          <WhatsAppButton matchId={matchId} />
        </div>
      )}
    </div>
  );
}

export default function TransactionsPage() {
  const { data: transactions, isLoading } = useMyTransactions();
  const confirmTx = useConfirmTransaction();
  const cancelTx = useCancelTransaction();
  const [error, setError] = useState("");

  if (isLoading) return <LoadingSpinner />;

  const handleConfirm = async (id: string) => {
    setError("");
    try {
      await confirmTx.mutateAsync(id);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to confirm transaction";
      // Auto-cancel stale transactions where the room occupant has changed
      if (message.toLowerCase().includes("occupant has changed")) {
        try {
          await cancelTx.mutateAsync(id);
          setError("This transaction is no longer valid and has been automatically cancelled.");
          return;
        } catch {
          // fall through to show original error
        }
      }
      setError(message);
    }
  };

  const handleCancel = async (id: string) => {
    setError("");
    try {
      await cancelTx.mutateAsync(id);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to cancel transaction"
      );
    }
  };

  return (
    <div>
      <h1 className="mb-6 text-xl font-bold text-gray-900">Transactions</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!transactions?.length ? (
        <EmptyState
          title="No transactions yet"
          description="Transactions are created when a match is accepted"
        />
      ) : (
        <div className="space-y-3">
          {transactions.map((tx) => (
            <TransactionCard
              key={tx.id}
              tx={tx}
              onConfirm={handleConfirm}
              onCancel={handleCancel}
              confirmPending={confirmTx.isPending}
              cancelPending={cancelTx.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}
