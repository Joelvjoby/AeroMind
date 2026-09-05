"use client";

import L from "leaflet";
import { useEffect } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { DEFAULT_CENTER } from "./MissionMap";
import { TRACK_ZOOM, type DroneTrackMapProps } from "./DroneTrackMap";

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

/** Drone pin, built from inline styles so no marker image assets are needed. */
const droneIcon = L.divIcon({
  className: "",
  html: `<div style="
    display:flex;align-items:center;justify-content:center;
    width:30px;height:30px;border-radius:9999px;
    background:#0ea5e9;color:#fff;font-size:15px;line-height:1;
    border:2px solid #082f49;box-shadow:0 0 0 6px rgba(14,165,233,.25);
  ">▲</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

/** Keeps the viewport following the drone as new frames arrive. */
function FollowDrone({ position }: { position: { lat: number; lon: number } | null }) {
  const map = useMap();

  useEffect(() => {
    if (position) map.setView([position.lat, position.lon], map.getZoom());
  }, [map, position]);

  return null;
}

export default function DroneTrackMapInner({
  position,
  trail = [],
  className,
}: DroneTrackMapProps) {
  const center: [number, number] = position
    ? [position.lat, position.lon]
    : DEFAULT_CENTER;

  return (
    <MapContainer
      center={center}
      zoom={position ? TRACK_ZOOM : 9}
      scrollWheelZoom
      className={className ?? "h-full w-full"}
      style={{ background: "#111827" }}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
      <FollowDrone position={position} />

      {trail.length > 1 && (
        <Polyline
          positions={trail.map((point) => [point.lat, point.lon])}
          pathOptions={{ color: "#0ea5e9", weight: 2, opacity: 0.6 }}
        />
      )}

      {position && (
        <Marker position={[position.lat, position.lon]} icon={droneIcon} />
      )}
    </MapContainer>
  );
}
