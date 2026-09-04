"use client";

import L from "leaflet";
import { MapContainer, Marker, Polyline, TileLayer, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  type MissionMapProps,
} from "./MissionMap";

// CARTO's dark basemap, rendered from OpenStreetMap data. Standard OSM
// tiles are light and read badly against the dark UI.
const TILE_URL =
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

/**
 * Numbered pin. Built as a divIcon with inline styles so it needs none of
 * Leaflet's default marker images, which bundlers resolve incorrectly.
 */
function numberedIcon(position: number) {
  return L.divIcon({
    className: "",
    html: `<div style="
      display:flex;align-items:center;justify-content:center;
      width:28px;height:28px;border-radius:9999px;
      background:#0ea5e9;color:#fff;
      font:600 12px/1 ui-sans-serif,system-ui,sans-serif;
      border:2px solid #082f49;box-shadow:0 1px 4px rgba(0,0,0,.5);
    ">${position}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function ClickHandler({
  onMapClick,
}: {
  onMapClick?: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(event) {
      onMapClick?.(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

export default function MissionMapInner({
  waypoints,
  onMapClick,
  className,
}: MissionMapProps) {
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      scrollWheelZoom
      className={className ?? "h-full w-full"}
      style={{ background: "#111827" }}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
      <ClickHandler onMapClick={onMapClick} />

      {waypoints.length > 1 && (
        <Polyline
          positions={waypoints.map((point) => [point.lat, point.lon])}
          pathOptions={{ color: "#0ea5e9", weight: 2, opacity: 0.7 }}
        />
      )}

      {waypoints.map((point, index) => (
        <Marker
          key={`${point.lat},${point.lon},${index}`}
          position={[point.lat, point.lon]}
          icon={numberedIcon(index + 1)}
        />
      ))}
    </MapContainer>
  );
}
