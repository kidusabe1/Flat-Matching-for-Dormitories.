import {
  useMyTransactions,
  useConfirmTransaction,
  useCancelTransaction,
} from "../hooks/useTransactions";
import StatusBadge from "../components/StatusBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { TransactionStatus, ListingType } from "../types";
import { useState } from "react";

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
      setError(
        err instanceof Error ? err.message : "Failed to confirm transaction"
      );
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
          {transactions.map((tx) => {
            const isPending = tx.status === TransactionStatus.PENDING;
            return (
              <div
                key={tx.id}
                className="rounded-lg border border-gray-200 bg-white p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
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
                          Rooms: {tx.party_a_room_id} &harr;{" "}
                          {tx.party_b_room_id}
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
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleConfirm(tx.id)}
                        disabled={confirmTx.isPending}
                        className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => handleCancel(tx.id)}
                        disabled={cancelTx.isPending}
                        className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
