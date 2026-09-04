"use client";

import dynamic from "next/dynamic";

export interface MapWaypoint {
  lat: number;
  lon: number;
}

export interface MissionMapProps {
  waypoints: MapWaypoint[];
  onMapClick?: (lat: number, lon: number) => void;
  className?: string;
}

/** Kerala, India. */
export const DEFAULT_CENTER: [number, number] = [10.0, 76.0];
export const DEFAULT_ZOOM = 9;

// Leaflet reaches for `window` at module scope, so the real map is only ever
// loaded in the browser. Rendering it on the server would throw.
const MissionMapInner = dynamic(() => import("./MissionMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-lg bg-gray-800 text-sm text-gray-400">
      Loading map…
    </div>
  ),
});

export default function MissionMap(props: MissionMapProps) {
  return <MissionMapInner {...props} />;
}
