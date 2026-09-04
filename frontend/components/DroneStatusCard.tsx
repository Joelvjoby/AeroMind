import type { DroneStatus } from "@/lib/api";

export interface DroneStatusCardProps {
  id: string;
  name: string;
  mavlink_id: number;
  status: DroneStatus;
  battery_level: number | null;
  fsm_state: string | null;
}

const STATUS_STYLES: Record<DroneStatus, string> = {
  IDLE: "bg-gray-700 text-gray-200",
  ASSIGNED: "bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/40",
  IN_FLIGHT: "bg-green-500/20 text-green-300 ring-1 ring-green-500/40",
  LOW_BATTERY: "bg-yellow-500/20 text-yellow-300 ring-1 ring-yellow-500/40",
  LOST: "bg-red-500/20 text-red-300 ring-1 ring-red-500/40",
};

/** Battery bar colour: green above 50%, yellow down to 20%, red below. */
function batteryColor(level: number) {
  if (level > 0.5) return "bg-green-500";
  if (level >= 0.2) return "bg-yellow-500";
  return "bg-red-500";
}

export default function DroneStatusCard({
  name,
  mavlink_id,
  status,
  battery_level,
  fsm_state,
}: DroneStatusCardProps) {
  const hasBattery = battery_level !== null && Number.isFinite(battery_level);
  const level = hasBattery ? Math.min(1, Math.max(0, battery_level)) : 0;
  const percent = Math.round(level * 100);

  return (
    <div className="rounded-lg bg-gray-800 p-4 ring-1 ring-gray-700/60">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-white">{name}</h3>
          <p className="mt-0.5 font-mono text-xs text-gray-400">
            MAVLink #{mavlink_id}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLES[status]}`}
        >
          {status.replace(/_/g, " ")}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-xs">
          <span className="text-gray-400">Battery</span>
          <span className="font-mono text-gray-300">
            {hasBattery ? `${percent}%` : "—"}
          </span>
        </div>
        <div
          className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-gray-700"
          role="progressbar"
          aria-valuenow={hasBattery ? percent : undefined}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${name} battery level`}
        >
          <div
            className={`h-full rounded-full transition-[width] duration-500 ${
              hasBattery ? batteryColor(level) : "bg-gray-600"
            }`}
            style={{ width: hasBattery ? `${percent}%` : "0%" }}
          />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-gray-700/60 pt-3 text-xs">
        <span className="text-gray-400">FSM state</span>
        <span className="font-mono text-sky-300">{fsm_state ?? "UNKNOWN"}</span>
      </div>
    </div>
  );
}
