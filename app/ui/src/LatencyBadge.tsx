import { formatElapsed } from "./types";

interface LatencyBadgeProps {
  elapsedMs: number;
  showWarning?: boolean;
}

export default function LatencyBadge({ elapsedMs, showWarning }: LatencyBadgeProps) {
  const seconds = elapsedMs / 1000;
  let level: "ok" | "warn" | "slow" = "ok";
  let label = "Within 5 s SLA";

  if (seconds > 8) {
    level = "slow";
    label = "Exceeds 8 s — investigate latency";
  } else if (seconds > 5 || showWarning) {
    level = "warn";
    label = "Above 5 s target — monitor";
  }

  return (
    <span
      className={`latency-badge latency-${level}`}
      aria-label={`Verification took ${formatElapsed(elapsedMs)}. ${label}`}
    >
      {formatElapsed(elapsedMs)} · {label}
    </span>
  );
}
