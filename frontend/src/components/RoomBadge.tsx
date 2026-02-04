import { RoomCategory } from "../types";

export const categoryLabels: Record<RoomCategory, string> = {
  [RoomCategory.PARK_SHARED_2BR]: "Park 100 — Shared 2BR",
  [RoomCategory.PARK_SHARED_3BR]: "Park 100 — Shared 3BR",
  [RoomCategory.PARK_STUDIO]: "Park 100 — Studio",
  [RoomCategory.PARK_COUPLES]: "Park 100 — Couples",
  [RoomCategory.ILANOT_SHARED_1BR]: "Ilanot — Shared 1BR",
  [RoomCategory.ILANOT_SHARED_2BR]: "Ilanot — Shared 2BR",
  [RoomCategory.ILANOT_PRIVATE]: "Ilanot — Private Room",
  [RoomCategory.ILANOT_SHARED_LARGE]: "Ilanot — Shared Large",
  [RoomCategory.ILANOT_STUDIO]: "Ilanot — Studio",
  [RoomCategory.ILANOT_COUPLES]: "Ilanot — Couples",
};

const categoryColors: Record<string, string> = {
  PARK: "bg-purple-100 text-purple-800",
  ILANOT: "bg-teal-100 text-teal-800",
};

interface RoomBadgeProps {
  category: RoomCategory;
}

export default function RoomBadge({ category }: RoomBadgeProps) {
  const complex = category.startsWith("PARK") ? "PARK" : "ILANOT";
  const colorClass = categoryColors[complex];
  const label = categoryLabels[category] ?? category;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {label}
    </span>
  );
}
