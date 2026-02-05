import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  useCreateLeaseTransfer,
  useCreateSwapRequest,
} from "../hooks/useListings";
import { useRooms } from "../hooks/useRooms";
import { RoomCategory, type Room } from "../types";
import { categoryLabels } from "../components/RoomBadge";

export default function CreateListingPage() {
  const navigate = useNavigate();
  const rooms = useRooms();
  const createLease = useCreateLeaseTransfer();
  const createSwap = useCreateSwapRequest();

  const [tab, setTab] = useState<"lease" | "swap">("lease");
  const [roomId, setRoomId] = useState("");
  const [leaseStart, setLeaseStart] = useState("");
  const [leaseEnd, setLeaseEnd] = useState("");
  const [moveInDate, setMoveInDate] = useState("");
  const [description, setDescription] = useState("");
  const [askingPrice, setAskingPrice] = useState("");
  const [desiredCategories, setDesiredCategories] = useState<RoomCategory[]>(
    []
  );
  const [desiredBuildings, setDesiredBuildings] = useState("");
  const [error, setError] = useState("");

  const toggleCategory = (cat: RoomCategory) => {
    setDesiredCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Date validation
    if (leaseStart && leaseEnd && leaseEnd <= leaseStart) {
      setError("Lease end date must be after the start date.");
      return;
    }
    if (moveInDate && leaseStart && moveInDate < leaseStart) {
      setError(
        tab === "lease"
          ? "Transfer date cannot be before the lease start date."
          : "Move-in date cannot be before the lease start date."
      );
      return;
    }
    if (moveInDate && leaseEnd && moveInDate > leaseEnd) {
      setError(
        tab === "lease"
          ? "Transfer date cannot be after the lease end date."
          : "Move-in date cannot be after the lease end date."
      );
      return;
    }

    try {
      if (tab === "lease") {
        await createLease.mutateAsync({
          room_id: roomId,
          lease_start_date: leaseStart,
          lease_end_date: leaseEnd,
          move_in_date: moveInDate || undefined,
          description: description || undefined,
          asking_price: askingPrice ? Number(askingPrice) : undefined,
        });
      } else {
        if (desiredCategories.length === 0) {
          setError("Select at least one desired room category");
          return;
        }
        await createSwap.mutateAsync({
          room_id: roomId,
          lease_start_date: leaseStart,
          lease_end_date: leaseEnd,
          move_in_date: moveInDate || undefined,
          description: description || undefined,
          desired_categories: desiredCategories,
          desired_buildings: desiredBuildings
            ? desiredBuildings.split(",").map((b) => b.trim())
            : undefined,
        });
      }
      navigate("/my-listings");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create listing";
      setError(message);
    }
  };

  const isPending = createLease.isPending || createSwap.isPending;

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-xl font-bold text-gray-900">
        Create New Listing
      </h1>

      {/* Tabs */}
      <div className="mb-6 flex rounded-lg border border-gray-200 bg-gray-50 p-1">
        <button
          onClick={() => setTab("lease")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition ${
            tab === "lease"
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Lease Transfer
        </button>
        <button
          onClick={() => setTab("swap")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition ${
            tab === "swap"
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Swap Request
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
      >
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Room Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Room
            </label>
            <select
              required
              value={roomId}
              onChange={(e) => setRoomId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="">Select a room type...</option>
              {(() => {
                const seen = new Set<string>();
                return rooms.data
                  ?.slice()
                  .sort((a, b) => a.building.localeCompare(b.building))
                  .filter((room) => {
                    const key = `${room.building}|${room.category}`;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                  })
                  .map((room: Room) => (
                    <option key={room.id} value={room.id}>
                      {room.building} — {categoryLabels[room.category] ?? room.category}
                    </option>
                  ));
              })()}
            </select>
          </div>

          {/* Lease Dates */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Lease Start Date
              </label>
              <input
                type="date"
                required
                value={leaseStart}
                onChange={(e) => setLeaseStart(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Lease End Date
              </label>
              <input
                type="date"
                required
                value={leaseEnd}
                min={leaseStart || undefined}
                onChange={(e) => setLeaseEnd(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Move-in / Transfer Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              {tab === "lease" ? "Transfer Date" : "Move-in Date"}
            </label>
            <p className="mt-0.5 text-xs text-gray-500">
              When do you want to {tab === "lease" ? "transfer" : "switch"}?
            </p>
            <input
              type="date"
              value={moveInDate}
              min={leaseStart || undefined}
              max={leaseEnd || undefined}
              onChange={(e) => setMoveInDate(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none sm:max-w-xs"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              placeholder="Add any details about the room or your preferences..."
            />
          </div>

          {/* Lease Transfer specific */}
          {tab === "lease" && (
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Asking Price (NIS)
              </label>
              <input
                type="number"
                min="0"
                value={askingPrice}
                onChange={(e) => setAskingPrice(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                placeholder="Optional"
              />
            </div>
          )}

          {/* Swap Request specific */}
          {tab === "swap" && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Desired Room Categories
                </label>
                <p className="mt-1 text-xs text-gray-500 font-medium">Park 100 Complex</p>
                <div className="mt-1 flex flex-wrap gap-3">
                  {([
                    [RoomCategory.PARK_SHARED_2BR, "Shared 2BR"],
                    [RoomCategory.PARK_SHARED_3BR, "Shared 3BR"],
                    [RoomCategory.PARK_STUDIO, "Studio"],
                    [RoomCategory.PARK_COUPLES, "Couples"],
                  ] as const).map(([cat, label]) => (
                    <label key={cat} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={desiredCategories.includes(cat)}
                        onChange={() => toggleCategory(cat)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{label}</span>
                    </label>
                  ))}
                </div>
                <p className="mt-3 text-xs text-gray-500 font-medium">Ilanot Complex</p>
                <div className="mt-1 flex flex-wrap gap-3">
                  {([
                    [RoomCategory.ILANOT_SHARED_1BR, "Shared 1BR"],
                    [RoomCategory.ILANOT_SHARED_2BR, "Shared 2BR"],
                    [RoomCategory.ILANOT_PRIVATE, "Private Room"],
                    [RoomCategory.ILANOT_SHARED_LARGE, "Shared Large"],
                    [RoomCategory.ILANOT_STUDIO, "Studio"],
                    [RoomCategory.ILANOT_COUPLES, "Couples"],
                  ] as const).map(([cat, label]) => (
                    <label key={cat} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={desiredCategories.includes(cat)}
                        onChange={() => toggleCategory(cat)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Desired Buildings
                </label>
                <input
                  type="text"
                  value={desiredBuildings}
                  onChange={(e) => setDesiredBuildings(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  placeholder="Comma-separated (e.g., Building A, Building B)"
                />
              </div>
            </>
          )}
        </div>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isPending ? "Creating..." : "Create Listing"}
          </button>
        </div>
      </form>
    </div>
  );
}
