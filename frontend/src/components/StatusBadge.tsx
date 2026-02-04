const statusColors: Record<string, string> = {
  OPEN: "bg-green-100 text-green-800",
  MATCHED: "bg-blue-100 text-blue-800",
  PARTIAL_MATCH: "bg-yellow-100 text-yellow-800",
  FULLY_MATCHED: "bg-blue-100 text-blue-800",
  PENDING_APPROVAL: "bg-yellow-100 text-yellow-800",
  COMPLETED: "bg-gray-100 text-gray-800",
  CANCELLED: "bg-red-100 text-red-800",
  EXPIRED: "bg-gray-100 text-gray-500",
  PROPOSED: "bg-yellow-100 text-yellow-800",
  ACCEPTED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  PENDING: "bg-yellow-100 text-yellow-800",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  FAILED: "bg-red-100 text-red-800",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colorClass = statusColors[status] || "bg-gray-100 text-gray-800";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
