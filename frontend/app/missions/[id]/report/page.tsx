"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getDrones, getMission, getMissionReport } from "@/lib/api";
import type { Drone, MissionDetail, MissionReport, TaskStatus } from "@/lib/api";
import {
  MISSION_STATUS_STYLES,
  TASK_STATUS_STYLES,
  formatTimestamp,
} from "@/lib/ui";

const TASK_STATUSES: TaskStatus[] = [
  "PENDING",
  "IN_PROGRESS",
  "COMPLETED",
  "FAILED",
];

export default function MissionReportPage() {
  const params = useParams<{ id: string }>();
  const missionId = params.id;

  const [report, setReport] = useState<MissionReport | null>(null);
  const [mission, setMission] = useState<MissionDetail | null>(null);
  const [drones, setDrones] = useState<Drone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        // The report carries waypoint ids but not their order, and drone ids
        // but not their names, so both are resolved alongside it.
        const [nextReport, nextMission, nextDrones] = await Promise.all([
          getMissionReport(missionId),
          getMission(missionId),
          getDrones(),
        ]);
        if (!active) return;
        setReport(nextReport);
        setMission(nextMission);
        setDrones(nextDrones);
        setError(null);
      } catch {
        if (active) setError("Could not load this mission report.");
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [missionId]);

  const droneNames = useMemo(
    () => new Map(drones.map((drone) => [drone.id, drone.name])),
    [drones],
  );
  const waypointOrder = useMemo(
    () =>
      new Map(
        (mission?.waypoints ?? []).map((point) => [
          point.id,
          point.sequence_order,
        ]),
      ),
    [mission],
  );

  const handleExport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `aeromind-mission-${missionId}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <p className="text-sm text-gray-400">Loading report…</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <p
          role="alert"
          className="rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30"
        >
          {error ?? "Report unavailable."}
        </p>
        <Link
          href="/dashboard"
          className="mt-4 inline-block text-sm text-sky-400 underline-offset-2 hover:underline"
        >
          ← Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {report.mission.name}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                MISSION_STATUS_STYLES[report.mission.status] ??
                "bg-gray-700 text-gray-200"
              }`}
            >
              {report.mission.status}
            </span>
            <span className="text-gray-400">
              Created {formatTimestamp(report.mission.created_at)}
            </span>
          </div>
          {mission?.description && (
            <p className="mt-3 max-w-2xl text-sm text-gray-300">
              {mission.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleExport}
            data-testid="export-json"
            className="rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-400"
          >
            Export JSON
          </button>
          <Link
            href={`/missions/${missionId}`}
            className="text-sm text-sky-400 underline-offset-2 hover:underline"
          >
            Live telemetry →
          </Link>
        </div>
      </header>

      <section className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {TASK_STATUSES.map((status) => (
          <div
            key={status}
            data-testid={`count-${status}`}
            className="rounded-lg bg-gray-800 p-5 ring-1 ring-gray-700/60"
          >
            <p className="text-xs text-gray-400">{status.replace(/_/g, " ")}</p>
            <p className="mt-1 text-3xl font-semibold tabular-nums text-white">
              {report.task_counts[status] ?? 0}
            </p>
          </div>
        ))}
      </section>

      <section className="mt-10">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Tasks</h2>
          <p className="text-xs text-gray-500">
            {report.total_waypoints} waypoint
            {report.total_waypoints === 1 ? "" : "s"} planned
          </p>
        </div>

        {report.tasks.length === 0 ? (
          <p className="mt-4 rounded-lg bg-gray-800/60 px-4 py-6 text-sm text-gray-400 ring-1 ring-gray-700/60">
            No tasks were assigned for this mission.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto rounded-lg ring-1 ring-gray-700/60">
            <table className="w-full text-left text-sm" data-testid="task-table">
              <thead className="bg-gray-800/80 text-xs uppercase tracking-wide text-gray-400">
                <tr>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Drone
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Waypoint
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Assigned
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Completed
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/60 bg-gray-800/40">
                {report.tasks.map((task) => {
                  const order = task.waypoint_id
                    ? waypointOrder.get(task.waypoint_id)
                    : undefined;
                  return (
                    <tr key={task.id} data-testid="task-row">
                      <td className="px-4 py-3 text-gray-100">
                        {task.drone_id
                          ? (droneNames.get(task.drone_id) ??
                            `${task.drone_id.slice(0, 8)}…`)
                          : "—"}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-300">
                        {order !== undefined ? `#${order + 1}` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            TASK_STATUS_STYLES[task.status] ??
                            "bg-gray-700 text-gray-200"
                          }`}
                        >
                          {task.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        {formatTimestamp(task.assigned_at)}
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        {formatTimestamp(task.completed_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-10">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Alerts</h2>
          <p className="text-xs text-gray-500">
            {report.unread_alerts} unread
          </p>
        </div>

        {report.alerts.length === 0 ? (
          <p className="mt-4 rounded-lg bg-gray-800/60 px-4 py-6 text-sm text-gray-400 ring-1 ring-gray-700/60">
            No alerts were raised during this mission.
          </p>
        ) : (
          <ul className="mt-4 space-y-3">
            {report.alerts.map((alert) => (
              <li
                key={alert.id}
                className={`rounded-lg bg-gray-800 p-4 ring-1 ring-gray-700/60 ${
                  alert.is_read
                    ? "border-l-4 border-transparent"
                    : "border-l-4 border-sky-500"
                }`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-amber-500/20 px-2.5 py-1 text-xs font-medium text-amber-300 ring-1 ring-amber-500/40">
                    {alert.alert_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(alert.created_at)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-100">{alert.message}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
