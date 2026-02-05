import { useState, useEffect, useMemo } from "react";
import { useProfile, useUpdateProfile } from "../hooks/useProfile";
import { useRoom, useRooms } from "../hooks/useRooms";
import { COUNTRY_CODES, parsePhone, isValidPhoneNumber } from "../utils/phone";

const CATEGORY_LABELS: Record<string, string> = {
  PARK_SHARED_2BR: "Shared 2-Bedroom",
  PARK_SHARED_3BR: "Shared 3-Bedroom",
  PARK_STUDIO: "Studio",
  PARK_COUPLES: "Couples",
  ILANOT_SHARED_1BR: "Shared 1-Bedroom",
  ILANOT_SHARED_2BR: "Shared 2-Bedroom",
  ILANOT_PRIVATE: "Private",
  ILANOT_SHARED_LARGE: "Shared Large",
  ILANOT_STUDIO: "Studio",
  ILANOT_COUPLES: "Couples",
};

function formatCategory(category: string) {
  return CATEGORY_LABELS[category] ?? category.replace(/_/g, " ");
}

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const { data: currentRoom } = useRoom(profile?.current_room_id);
  const { data: rooms } = useRooms({ is_active: true });
  const updateProfile = useUpdateProfile();

  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("+972");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [roomId, setRoomId] = useState("");

  // Group rooms by building → category, picking one representative room ID per category
  const roomOptions = useMemo(() => {
    if (!rooms) return [];
    const seen = new Map<string, { id: string; building: string; category: string }>();
    for (const r of rooms) {
      const key = `${r.building}|${r.category}`;
      if (!seen.has(key)) {
        seen.set(key, { id: r.id, building: r.building, category: r.category });
      }
    }
    const entries = [...seen.values()];
    entries.sort((a, b) => a.building.localeCompare(b.building) || a.category.localeCompare(b.category));
    return entries;
  }, [rooms]);

  // Find the category key for the currently selected room
  const selectedCategory = useMemo(() => {
    if (!roomId || !rooms) return "";
    const room = rooms.find((r) => r.id === roomId);
    if (!room) return "";
    return `${room.building}|${room.category}`;
  }, [roomId, rooms]);

  const handleCategoryChange = (key: string) => {
    const option = roomOptions.find((o) => `${o.building}|${o.category}` === key);
    setRoomId(option?.id ?? "");
  };

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name);
      const parsed = parsePhone(profile.phone);
      setCountryCode(parsed.countryCode);
      setPhoneNumber(parsed.number);
      setRoomId(profile.current_room_id ?? "");
    }
  }, [profile]);

  const phoneValid = isValidPhoneNumber(phoneNumber);

  const handleSave = async () => {
    if (!phoneValid) return;
    await updateProfile.mutateAsync({
      full_name: fullName,
      phone: countryCode + phoneNumber.replace(/[\s-]/g, ""),
      current_room_id: roomId || undefined,
    });
    setEditing(false);
  };

  const handleCancel = () => {
    if (profile) {
      setFullName(profile.full_name);
      const parsed = parsePhone(profile.phone);
      setCountryCode(parsed.countryCode);
      setPhoneNumber(parsed.number);
      setRoomId(profile.current_room_id ?? "");
    }
    setEditing(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="py-20 text-center text-gray-500">
        Profile not found.
      </div>
    );
  }

  const roomLabel = currentRoom
    ? `${currentRoom.building} - ${formatCategory(currentRoom.category)}`
    : null;

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
          >
            Edit Profile
          </button>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        {/* Avatar / Header */}
        <div className="flex items-center gap-4 border-b border-gray-100 p-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-2xl font-bold text-blue-600">
            {profile.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            {editing ? (
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-lg font-semibold text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            ) : (
              <h2 className="text-lg font-semibold text-gray-900">
                {profile.full_name}
              </h2>
            )}
            <p className="text-sm text-gray-500">{profile.email}</p>
          </div>
        </div>

        {/* Details */}
        <div className="divide-y divide-gray-100">
          <DetailRow label="Student ID" value={profile.student_id} />

          <div className="flex items-center justify-between px-6 py-4">
            <div className="w-full">
              <p className="text-sm font-medium text-gray-500">Phone</p>
              {editing ? (
                <div className="mt-1 flex gap-2">
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className="w-28 rounded-lg border border-gray-300 px-2 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  >
                    {COUNTRY_CODES.map((cc) => (
                      <option key={cc.code} value={cc.code}>
                        {cc.label}
                      </option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className={`flex-1 rounded-lg border px-3 py-1.5 text-sm text-gray-900 focus:outline-none focus:ring-1 ${
                      !phoneValid && phoneNumber.length > 0
                        ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                        : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    }`}
                    placeholder="501234567"
                  />
                </div>
              ) : (
                <p className="mt-0.5 text-sm text-gray-900">{profile.phone || "Not set"}</p>
              )}
              {editing && !phoneValid && phoneNumber.length > 0 && (
                <p className="mt-1 text-xs text-red-600">
                  Enter a valid phone number (7-15 digits).
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between px-6 py-4">
            <div className="w-full">
              <p className="text-sm font-medium text-gray-500">Current Room</p>
              {editing ? (
                <select
                  value={selectedCategory}
                  onChange={(e) => handleCategoryChange(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">No room assigned</option>
                  {roomOptions.map((o) => (
                    <option key={`${o.building}|${o.category}`} value={`${o.building}|${o.category}`}>
                      {o.building} - {formatCategory(o.category)}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="mt-0.5 text-sm text-gray-900">
                  {roomLabel ?? "No room assigned"}
                </p>
              )}
            </div>
          </div>

          {currentRoom && !editing && (
            <div className="px-6 py-4">
              <p className="text-sm font-medium text-gray-500">Room Details</p>
              <div className="mt-2 rounded-lg bg-gray-50 p-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">Building:</span>{" "}
                    <span className="font-medium text-gray-900">{currentRoom.building}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Type:</span>{" "}
                    <span className="font-medium text-gray-900">
                      {formatCategory(currentRoom.category)}
                    </span>
                  </div>
                </div>
                {currentRoom.description && (
                  <p className="mt-2 text-sm text-gray-600">{currentRoom.description}</p>
                )}
                {currentRoom.amenities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {currentRoom.amenities.map((a) => (
                      <span
                        key={a}
                        className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                      >
                        {a}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <DetailRow
            label="Member Since"
            value={
              profile.created_at
                ? new Date(profile.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })
                : "Unknown"
            }
          />
        </div>

        {/* Edit actions */}
        {editing && (
          <div className="flex items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
            <button
              onClick={handleCancel}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={updateProfile.isPending || !fullName.trim() || !phoneValid}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {updateProfile.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-6 py-4">
      <div>
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <p className="mt-0.5 text-sm text-gray-900">{value}</p>
      </div>
    </div>
  );
}
