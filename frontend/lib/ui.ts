/** Display helpers shared across the dashboard, telemetry and report pages. */

export const FSM_STATE_STYLES: Record<string, string> = {
  NORMAL: "bg-green-500/20 text-green-300 ring-1 ring-green-500/40",
  REPLANNING: "bg-yellow-500/20 text-yellow-300 ring-1 ring-yellow-500/40",
  LOW_BATTERY_RETURN: "bg-orange-500/20 text-orange-300 ring-1 ring-orange-500/40",
  BLOCKED_HOLD: "bg-red-500/20 text-red-300 ring-1 ring-red-500/40",
  COMPLETE: "bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/40",
};

export function fsmStyle(state: string | null | undefined): string {
  if (!state) return "bg-gray-700 text-gray-300";
  return FSM_STATE_STYLES[state] ?? "bg-gray-700 text-gray-300";
}

export const MISSION_STATUS_STYLES: Record<string, string> = {
  PLANNED: "bg-gray-700 text-gray-200",
  ACTIVE: "bg-green-500/20 text-green-300 ring-1 ring-green-500/40",
  COMPLETED: "bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/40",
  ABORTED: "bg-red-500/20 text-red-300 ring-1 ring-red-500/40",
};

export const TASK_STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-gray-700 text-gray-200",
  IN_PROGRESS: "bg-yellow-500/20 text-yellow-300 ring-1 ring-yellow-500/40",
  COMPLETED: "bg-green-500/20 text-green-300 ring-1 ring-green-500/40",
  FAILED: "bg-red-500/20 text-red-300 ring-1 ring-red-500/40",
};

/** Battery bar colour: green above 50%, yellow down to 20%, red below. */
export function batteryColor(level: number): string {
  if (level > 0.5) return "bg-green-500";
  if (level >= 0.2) return "bg-yellow-500";
  return "bg-red-500";
}

/**
 * Parse a timestamp from the API.
 *
 * FastAPI serialises the naive UTC datetimes stored by SQLAlchemy without a
 * zone suffix, and JavaScript reads those as local time. Anything lacking an
 * offset is therefore pinned to UTC before parsing.
 */
export function parseServerDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  const parsed = new Date(hasZone ? value : `${value}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatTimestamp(value: string | null | undefined): string {
  const date = parseServerDate(value);
  return date ? date.toLocaleString() : "—";
}

export function formatTime(value: string | null | undefined): string {
  const date = parseServerDate(value);
  return date ? date.toLocaleTimeString() : "—";
}
