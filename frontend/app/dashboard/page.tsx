"use client";

import { useCallback, useEffect, useState } from "react";

import DroneStatusCard from "@/components/DroneStatusCard";
import { getAlerts, getDrones, getMissions } from "@/lib/api";
import type { Alert, Drone, Mission } from "@/lib/api";

const REFRESH_INTERVAL_MS = 5000;

/** In play: planned or under way, as opposed to finished or aborted. */
const ACTIVE_MISSION_STATUSES = new Set(["PLANNED", "ACTIVE"]);

function StatCard({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-lg bg-gray-800 p-5 ring-1 ring-gray-700/60">
      <p className="text-sm text-gray-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold tabular-nums text-white">
        {value ?? "—"}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const [drones, setDrones] = useState<Drone[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [nextDrones, nextMissions, nextAlerts] = await Promise.all([
        getDrones(),
        getMissions(),
        getAlerts(),
      ]);
      setDrones(nextDrones);
      setMissions(nextMissions);
      setAlerts(nextAlerts);
      setError(null);
    } catch {
      // Keep the last good data on screen rather than blanking the board.
      setError("Could not reach the AeroMind backend at localhost:8000.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;

    const tick = async () => {
      if (active) await load();
    };

    void tick();
    const timer = setInterval(tick, REFRESH_INTERVAL_MS);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [load]);

  const activeMissions = missions.filter((mission) =>
    ACTIVE_MISSION_STATUSES.has(mission.status),
  ).length;
  const unreadAlerts = alerts.filter((alert) => !alert.is_read).length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <header className="flex items-baseline justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-xs text-gray-500">
          Refreshing every {REFRESH_INTERVAL_MS / 1000}s
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30"
        >
          {error}
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          label="Active missions"
          value={loading ? null : activeMissions}
        />
        <StatCard label="Unread alerts" value={loading ? null : unreadAlerts} />
      </div>

      <section className="mt-10">
        <h2 className="text-lg font-semibold tracking-tight">Fleet</h2>

        {loading ? (
          <p className="mt-4 text-sm text-gray-400">Loading fleet…</p>
        ) : drones.length === 0 ? (
          <p className="mt-4 rounded-lg bg-gray-800/60 px-4 py-6 text-sm text-gray-400 ring-1 ring-gray-700/60">
            No drones registered yet.
          </p>
        ) : (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {drones.map((drone) => (
              <DroneStatusCard
                key={drone.id}
                id={drone.id}
                name={drone.name}
                mavlink_id={drone.mavlink_id}
                status={drone.status}
                battery_level={drone.battery_level}
                fsm_state={drone.fsm_state}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
