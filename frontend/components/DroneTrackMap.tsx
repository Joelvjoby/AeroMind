"use client";

import dynamic from "next/dynamic";

export interface TrackPoint {
  lat: number;
  lon: number;
}

export interface DroneTrackMapProps {
  /** Latest known position, or null before the first frame arrives. */
  position: TrackPoint | null;
  /** Recent positions, oldest first, drawn as a trail. */
  trail?: TrackPoint[];
  className?: string;
}

export const TRACK_ZOOM = 15;

// Leaflet touches `window` at module scope, so the map is browser-only.
const DroneTrackMapInner = dynamic(() => import("./DroneTrackMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-lg bg-gray-800 text-sm text-gray-400">
      Loading map…
    </div>
  ),
});

export default function DroneTrackMap(props: DroneTrackMapProps) {
  return <DroneTrackMapInner {...props} />;
}
