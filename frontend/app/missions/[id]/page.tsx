"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import DroneTrackMap, { type TrackPoint } from "@/components/DroneTrackMap";
import TelemetryStreamWidget, {
  type TelemetryEntry,
} from "@/components/TelemetryStreamWidget";
import { getDrones } from "@/lib/api";
import type { Drone } from "@/lib/api";
import { fsmStyle } from "@/lib/ui";

const TRAIL_LENGTH = 60;
const HISTORY_LENGTH = 10;

interface Transition {
  from: string | null;
  to: string;
  at: string;
}

export default function LiveTelemetryPage() {
  const params = useParams<{ id: string }>();
  const droneId = params.id;

  const [drone, setDrone] = useState<Drone | null>(null);
  const [position, setPosition] = useState<TrackPoint | null>(null);
  const [trail, setTrail] = useState<TrackPoint[]>([]);
  const [history, setHistory] = useState<Transition[]>([]);

  // Compared against each frame's state without re-triggering the callback.
  const lastStateRef = useRef<string | null>(null);

  useEffect(() => {
    let active = true;
    getDrones()
      .then((drones) => {
        if (active) setDrone(drones.find((d) => d.id === droneId) ?? null);
      })
      .catch(() => {
        // The page still works without the drone's name.
      });
    return () => {
      active = false;
    };
  }, [droneId]);

  const handleTelemetry = useCallback((entry: TelemetryEntry) => {
    const point = { lat: entry.latitude, lon: entry.longitude };
    setPosition(point);
    setTrail((current) => [...current, point].slice(-TRAIL_LENGTH));

    if (entry.fsm_state !== lastStateRef.current) {
      const from = lastStateRef.current;
      lastStateRef.current = entry.fsm_state;
      setHistory((current) =>
        [{ from, to: entry.fsm_state, at: entry.timestamp }, ...current].slice(
          0,
          HISTORY_LENGTH,
        ),
      );
    }
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Live Telemetry
          </h1>
          <p className="mt-1 font-mono text-xs text-gray-500">{droneId}</p>
        </div>
        <Link
          href="/dashboard"
          className="text-sm text-sky-400 underline-offset-2 hover:underline"
        >
          ← Back to dashboard
        </Link>
      </header>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="h-112 overflow-hidden rounded-lg ring-1 ring-gray-700/60">
            <DroneTrackMap position={position} trail={trail} />
          </div>
        </div>

        <div className="space-y-6">
          <TelemetryStreamWidget
            droneId={droneId}
            onTelemetryUpdate={handleTelemetry}
            droneName={drone?.name}
            mavlinkId={drone?.mavlink_id}
          />

          <section
            className="rounded-lg bg-gray-800 p-5 ring-1 ring-gray-700/60"
            data-testid="fsm-history"
          >
            <h2 className="text-sm font-semibold text-white">
              State history
              <span className="ml-2 font-normal text-gray-500">
                (last {HISTORY_LENGTH})
              </span>
            </h2>

            {history.length === 0 ? (
              <p className="mt-3 text-xs text-gray-400">
                Waiting for the first state change…
              </p>
            ) : (
              <ol className="mt-3 space-y-2">
                {history.map((transition, index) => (
                  <li
                    key={`${transition.at}-${index}`}
                    className="flex items-center gap-2 text-xs"
                    data-testid="fsm-history-entry"
                  >
                    <span className="font-mono text-gray-500">
                      {new Date(transition.at).toLocaleTimeString()}
                    </span>
                    {transition.from && (
                      <>
                        <span className="text-gray-500">
                          {transition.from}
                        </span>
                        <span aria-hidden className="text-gray-600">
                          →
                        </span>
                      </>
                    )}
                    <span
                      className={`rounded-full px-2 py-0.5 font-medium ${fsmStyle(
                        transition.to,
                      )}`}
                    >
                      {transition.to}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
