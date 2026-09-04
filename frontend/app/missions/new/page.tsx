"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import MissionMap, { type MapWaypoint } from "@/components/MissionMap";
import { createMission } from "@/lib/api";

/** Map clicks carry no elevation, so every waypoint starts at this height. */
const DEFAULT_ALTITUDE_M = 50;

export default function NewMissionPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [waypoints, setWaypoints] = useState<MapWaypoint[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addWaypoint = useCallback((lat: number, lon: number) => {
    setWaypoints((current) => [...current, { lat, lon }]);
  }, []);

  const removeWaypoint = (index: number) => {
    setWaypoints((current) => current.filter((_, i) => i !== index));
  };

  const canSubmit = name.trim().length > 0 && waypoints.length > 0 && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);

    try {
      await createMission({
        name: name.trim(),
        description: description.trim() || null,
        waypoints: waypoints.map((point) => ({
          latitude: point.lat,
          longitude: point.lon,
          altitude: DEFAULT_ALTITUDE_M,
        })),
      });
      router.push("/dashboard");
    } catch {
      setError(
        "Could not create the mission. Check that the backend is running at localhost:8000.",
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-2xl font-semibold tracking-tight">New Mission</h1>
      <p className="mt-1 text-sm text-gray-400">
        Click the map to drop waypoints in flight order.
      </p>

      <form onSubmit={handleSubmit} className="mt-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-1">
            <div>
              <label
                htmlFor="mission-name"
                className="block text-sm font-medium text-gray-300"
              >
                Mission name
              </label>
              <input
                id="mission-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Perimeter sweep"
                className="mt-1.5 w-full rounded-md bg-gray-800 px-3 py-2 text-sm text-white ring-1 ring-gray-700 outline-none placeholder:text-gray-500 focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label
                htmlFor="mission-description"
                className="block text-sm font-medium text-gray-300"
              >
                Description
              </label>
              <textarea
                id="mission-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
                placeholder="What is this mission for?"
                className="mt-1.5 w-full resize-y rounded-md bg-gray-800 px-3 py-2 text-sm text-white ring-1 ring-gray-700 outline-none placeholder:text-gray-500 focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <div className="flex items-baseline justify-between">
                <h2 className="text-sm font-medium text-gray-300">
                  Waypoints ({waypoints.length})
                </h2>
                {waypoints.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setWaypoints([])}
                    className="text-xs text-gray-400 underline-offset-2 hover:text-gray-200 hover:underline"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {waypoints.length === 0 ? (
                <p className="mt-2 rounded-md bg-gray-800/60 px-3 py-4 text-xs text-gray-400 ring-1 ring-gray-700/60">
                  No waypoints yet — click the map to add one.
                </p>
              ) : (
                <ol className="mt-2 space-y-1.5">
                  {waypoints.map((point, index) => (
                    <li
                      key={`${point.lat}-${point.lon}-${index}`}
                      className="flex items-center gap-3 rounded-md bg-gray-800 px-3 py-2 ring-1 ring-gray-700/60"
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-500 text-xs font-semibold text-white">
                        {index + 1}
                      </span>
                      <span className="flex-1 font-mono text-xs text-gray-300">
                        {point.lat.toFixed(5)}, {point.lon.toFixed(5)}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeWaypoint(index)}
                        aria-label={`Remove waypoint ${index + 1}`}
                        className="shrink-0 rounded px-1.5 text-gray-500 hover:bg-gray-700 hover:text-red-300"
                      >
                        ✕
                      </button>
                    </li>
                  ))}
                </ol>
              )}
              <p className="mt-2 text-xs text-gray-500">
                Altitude defaults to {DEFAULT_ALTITUDE_M} m.
              </p>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="h-112 overflow-hidden rounded-lg ring-1 ring-gray-700/60 lg:h-full lg:min-h-128">
              <MissionMap waypoints={waypoints} onMapClick={addWaypoint} />
            </div>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="mt-6 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30"
          >
            {error}
          </p>
        )}

        <div className="mt-6 flex items-center gap-4">
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded-md bg-sky-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-gray-700 disabled:text-gray-400"
          >
            {submitting ? "Creating…" : "Create mission"}
          </button>
          {!canSubmit && !submitting && (
            <span className="text-xs text-gray-500">
              Add a name and at least one waypoint.
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
