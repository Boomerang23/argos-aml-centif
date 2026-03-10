import { Badge } from "@/components/ui/badge";

export type Status = "DRAFT" | "ORANGE" | "GREEN" | "RED";

const STATUS_CONFIG: Record<
  Status,
  { label: string; className: string }
> = {
  DRAFT: {
    label: "Draft",
    className: "bg-gray-200 text-gray-900",
  },
  ORANGE: {
    label: "Orange",
    className: "bg-orange-500 text-white",
  },
  GREEN: {
    label: "Green",
    className: "bg-emerald-600 text-white",
  },
  RED: {
    label: "Red",
    className: "bg-red-600 text-white",
  },
};

export function StatusBadge({ status }: { status: Status }) {
  const config = STATUS_CONFIG[status];

  return (
    <Badge className={config.className}>
      {config.label}
    </Badge>
  );
}