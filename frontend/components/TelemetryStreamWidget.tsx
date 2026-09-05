"use client";

import { useEffect, useRef, useState } from "react";

import { batteryColor, fsmStyle } from "@/lib/ui";

export interface TelemetryEntry {
  drone_id: string;
  latitude: number;
  longitude: number;
  altitude: number;
  battery_level: number;
  fsm_state: string;
  speed: number;
  timestamp: string;
}

export interface TelemetryStreamWidgetProps {
  droneId: string;
  onTelemetryUpdate?: (entry: TelemetryEntry) => void;
  droneName?: string;
  mavlinkId?: number;
}

export const WS_BASE_URL = "ws://localhost:8000/api/v1";
const RECONNECT_DELAY_MS = 3000;

type ConnectionState = "connecting" | "open" | "reconnecting";

export default function TelemetryStreamWidget({
  droneId,
  onTelemetryUpdate,
  droneName,
  mavlinkId,
}: TelemetryStreamWidgetProps) {
  const [entry, setEntry] = useState<TelemetryEntry | null>(null);
  const [connection, setConnection] = useState<ConnectionState>("connecting");

  // Held in a ref so a parent re-rendering with a new callback identity does
  // not tear down and rebuild the socket.
  const onUpdateRef = useRef(onTelemetryUpdate);
  useEffect(() => {
    onUpdateRef.current = onTelemetryUpdate;
  }, [onTelemetryUpdate]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let disposed = false;

    const connect = () => {
      if (disposed) return;

      socket = new WebSocket(
        `${WS_BASE_URL}/telemetry/stream?drone_id=${encodeURIComponent(droneId)}`,
      );

      socket.onopen = () => {
        if (!disposed) setConnection("open");
      };

      socket.onmessage = (event) => {
        if (disposed) return;
        try {
          const parsed = JSON.parse(event.data as string) as TelemetryEntry;
          setEntry(parsed);
          onUpdateRef.current?.(parsed);
        } catch {
          // A malformed frame should not kill the stream.
        }
      };

      socket.onclose = () => {
        if (disposed) return;
        setConnection("reconnecting");
        retryTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      // onerror is always followed by onclose, which owns the retry.
      socket.onerror = () => socket?.close();
    };

    connect();

    return () => {
      disposed = true;
      if (retryTimer) clearTimeout(retryTimer);
      // Drop handlers first so teardown does not schedule a reconnect.
      if (socket) {
        socket.onclose = null;
        socket.onerror = null;
        socket.onmessage = null;
        socket.close();
      }
    };
  }, [droneId]);

  const battery = entry ? Math.min(1, Math.max(0, entry.battery_level)) : 0;
  const percent = Math.round(battery * 100);

  return (
    <div
      className="rounded-lg bg-gray-800 p-5 ring-1 ring-gray-700/60"
      data-testid="telemetry-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-white">
            {droneName ?? "Drone"}
          </h2>
          <p className="mt-0.5 font-mono text-xs text-gray-400">
            {mavlinkId !== undefined
              ? `MAVLink #${mavlinkId}`
              : `${droneId.slice(0, 8)}…`}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-1 text-xs font-medium ${
            connection === "open"
              ? "bg-green-500/20 text-green-300"
              : "bg-yellow-500/20 text-yellow-300"
          }`}
          data-testid="connection-state"
        >
          {connection === "open" ? "● Live" : "○ Reconnecting"}
        </span>
      </div>

      <div className="mt-5">
        <p className="text-xs text-gray-400">FSM state</p>
        <span
          className={`mt-1.5 inline-block rounded-full px-3 py-1 text-sm font-medium ${fsmStyle(
            entry?.fsm_state,
          )}`}
          data-testid="fsm-state"
        >
          {entry?.fsm_state ?? "—"}
        </span>
      </div>

      <div className="mt-5">
        <div className="flex items-baseline justify-between text-xs">
          <span className="text-gray-400">Battery</span>
          <span className="font-mono text-gray-300" data-testid="battery-percent">
            {entry ? `${percent}%` : "—"}
          </span>
        </div>
        <div
          className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-gray-700"
          role="progressbar"
          aria-valuenow={entry ? percent : undefined}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Battery level"
        >
          <div
            className={`h-full rounded-full transition-[width] duration-500 ${
              entry ? batteryColor(battery) : "bg-gray-600"
            }`}
            style={{ width: entry ? `${percent}%` : "0%" }}
          />
        </div>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-gray-700/60 pt-4 text-sm">
        <div>
          <dt className="text-xs text-gray-400">Latitude</dt>
          <dd className="font-mono text-gray-200" data-testid="latitude">
            {entry ? entry.latitude.toFixed(6) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-400">Longitude</dt>
          <dd className="font-mono text-gray-200" data-testid="longitude">
            {entry ? entry.longitude.toFixed(6) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-400">Altitude</dt>
          <dd className="font-mono text-gray-200">
            {entry ? `${entry.altitude.toFixed(1)} m` : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-400">Speed</dt>
          <dd className="font-mono text-gray-200">
            {entry ? `${entry.speed.toFixed(2)} m/s` : "—"}
          </dd>
        </div>
      </dl>

      <p className="mt-4 border-t border-gray-700/60 pt-3 text-xs text-gray-500">
        Last updated{" "}
        <span className="font-mono text-gray-400" data-testid="last-updated">
          {entry ? new Date(entry.timestamp).toLocaleTimeString() : "—"}
        </span>
      </p>
    </div>
  );
}
