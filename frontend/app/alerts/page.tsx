"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { getAlerts, getDrones, getMissions, markAlertRead } from "@/lib/api";
import type { Alert, Drone, Mission } from "@/lib/api";
import { formatTimestamp } from "@/lib/ui";

const REFRESH_INTERVAL_MS = 10000;

const FILTERS = ["All", "Unread", "Read"] as const;
type Filter = (typeof FILTERS)[number];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [drones, setDrones] = useState<Drone[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [filter, setFilter] = useState<Filter>("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marking, setMarking] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [nextAlerts, nextDrones, nextMissions] = await Promise.all([
        getAlerts(),
        getDrones(),
        getMissions(),
      ]);
      setAlerts(nextAlerts);
      setDrones(nextDrones);
      setMissions(nextMissions);
      setError(null);
    } catch {
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

  // Alerts carry ids, not names, so the labels are resolved client side.
  const droneNames = useMemo(
    () => new Map(drones.map((drone) => [drone.id, drone.name])),
    [drones],
  );
  const missionNames = useMemo(
    () => new Map(missions.map((mission) => [mission.id, mission.name])),
    [missions],
  );

  const handleMarkRead = async (id: string) => {
    setMarking(id);
    // Optimistic: flip locally, then reconcile with the server's copy.
    setAlerts((current) =>
      current.map((alert) =>
        alert.id === id ? { ...alert, is_read: true } : alert,
      ),
    );
    try {
      const updated = await markAlertRead(id);
      setAlerts((current) =>
        current.map((alert) => (alert.id === id ? updated : alert)),
      );
      setError(null);
    } catch {
      setAlerts((current) =>
        current.map((alert) =>
          alert.id === id ? { ...alert, is_read: false } : alert,
        ),
      );
      setError("Could not mark that alert as read.");
    } finally {
      setMarking(null);
    }
  };

  const unreadCount = alerts.filter((alert) => !alert.is_read).length;
  const visible = alerts.filter((alert) =>
    filter === "All" ? true : filter === "Unread" ? !alert.is_read : alert.is_read,
  );

  const countFor = (value: Filter) =>
    value === "All"
      ? alerts.length
      : value === "Unread"
        ? unreadCount
        : alerts.length - unreadCount;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
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

      <div className="mt-6 flex gap-1" role="tablist" aria-label="Filter alerts">
        {FILTERS.map((value) => {
          const active = filter === value;
          return (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setFilter(value)}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                active
                  ? "bg-gray-800 font-medium text-white ring-1 ring-gray-700"
                  : "text-gray-400 hover:bg-gray-800/60 hover:text-gray-100"
              }`}
            >
              {value}
              <span className="ml-1.5 font-mono text-xs text-gray-500">
                {countFor(value)}
              </span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <p className="mt-6 text-sm text-gray-400">Loading alerts…</p>
      ) : visible.length === 0 ? (
        <p className="mt-6 rounded-lg bg-gray-800/60 px-4 py-6 text-sm text-gray-400 ring-1 ring-gray-700/60">
          {alerts.length === 0
            ? "No alerts have been raised yet."
            : `No ${filter.toLowerCase()} alerts.`}
        </p>
      ) : (
        <ul className="mt-6 space-y-3" data-testid="alert-list">
          {visible.map((alert) => (
            <li
              key={alert.id}
              data-testid="alert-item"
              data-read={alert.is_read}
              className={`rounded-lg bg-gray-800 p-4 ring-1 ring-gray-700/60 ${
                alert.is_read
                  ? "border-l-4 border-transparent"
                  : "border-l-4 border-sky-500"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-amber-500/20 px-2.5 py-1 text-xs font-medium text-amber-300 ring-1 ring-amber-500/40">
                      {alert.alert_type}
                    </span>
                    {!alert.is_read && (
                      <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-xs font-medium text-sky-300">
                        Unread
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-sm text-gray-100">{alert.message}</p>

                  <dl className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-gray-400">
                    <div className="flex gap-1.5">
                      <dt>Drone:</dt>
                      <dd className="text-gray-300">
                        {alert.drone_id
                          ? (droneNames.get(alert.drone_id) ??
                            `${alert.drone_id.slice(0, 8)}…`)
                          : "—"}
                      </dd>
                    </div>
                    <div className="flex gap-1.5">
                      <dt>Mission:</dt>
                      <dd className="text-gray-300">
                        {alert.mission_id
                          ? (missionNames.get(alert.mission_id) ??
                            `${alert.mission_id.slice(0, 8)}…`)
                          : "—"}
                      </dd>
                    </div>
                    <div className="flex gap-1.5">
                      <dt>Raised:</dt>
                      <dd className="text-gray-300">
                        {formatTimestamp(alert.created_at)}
                      </dd>
                    </div>
                  </dl>
                </div>

                {!alert.is_read && (
                  <button
                    type="button"
                    onClick={() => handleMarkRead(alert.id)}
                    disabled={marking === alert.id}
                    data-testid="mark-read"
                    className="shrink-0 rounded-md bg-gray-700 px-3 py-1.5 text-xs font-medium text-gray-100 transition-colors hover:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {marking === alert.id ? "Marking…" : "Mark as read"}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
