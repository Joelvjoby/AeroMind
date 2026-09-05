import axios from "axios";

export const API_BASE_URL = "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/* Types mirror the FastAPI response schemas in backend/app/schemas/. */

export type MissionStatus = "PLANNED" | "ACTIVE" | "COMPLETED" | "ABORTED";

export type DroneStatus =
  | "IDLE"
  | "ASSIGNED"
  | "IN_FLIGHT"
  | "LOW_BATTERY"
  | "LOST";

export type TaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED";

export interface WaypointInput {
  latitude: number;
  longitude: number;
  altitude: number;
  /** Defaults to the waypoint's position in the submitted list. */
  sequence_order?: number;
}

export interface MissionCreate {
  name: string;
  description?: string | null;
  waypoints: WaypointInput[];
  /** Optional until authentication exists. */
  created_by?: string | null;
}

export interface Mission {
  id: string;
  name: string;
  status: MissionStatus;
  created_at: string | null;
  /** 0 on a freshly created mission's own response; real elsewhere. */
  task_count: number;
}

export interface Waypoint {
  id: string;
  sequence_order: number;
  latitude: number;
  longitude: number;
  altitude: number;
}

export interface MissionDetail extends Mission {
  description: string | null;
  waypoints: Waypoint[];
}

export interface PathPoint {
  lat: number;
  lon: number;
}

export interface Task {
  id: string;
  drone_id: string | null;
  waypoint_id: string | null;
  status: TaskStatus;
  assigned_at: string | null;
  completed_at: string | null;
  /** Route from A*; null when planning failed or was skipped. */
  planned_path: PathPoint[] | null;
}

export interface Drone {
  id: string;
  name: string;
  mavlink_id: number;
  status: DroneStatus;
  battery_level: number | null;
  current_lat: number | null;
  current_lon: number | null;
  /** Live FSM state, read from the backend's in-memory registry. */
  fsm_state: string | null;
}

export interface Alert {
  id: string;
  mission_id: string | null;
  drone_id: string | null;
  alert_type: string;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

export interface MissionReport {
  mission: Mission;
  total_waypoints: number;
  task_counts: Record<TaskStatus, number>;
  tasks: Task[];
  alerts: Alert[];
  unread_alerts: number;
}

export async function createMission(data: MissionCreate): Promise<Mission> {
  const response = await client.post<Mission>("/missions", data);
  return response.data;
}

export async function getMissions(status?: MissionStatus): Promise<Mission[]> {
  const response = await client.get<Mission[]>("/missions", {
    params: status ? { status } : undefined,
  });
  return response.data;
}

export async function getMission(id: string): Promise<MissionDetail> {
  const response = await client.get<MissionDetail>(`/missions/${id}`);
  return response.data;
}

export async function getMissionReport(id: string): Promise<MissionReport> {
  const response = await client.get<MissionReport>(`/missions/${id}/report`);
  return response.data;
}

export async function getDrones(): Promise<Drone[]> {
  const response = await client.get<Drone[]>("/drones");
  return response.data;
}

export async function getAlerts(): Promise<Alert[]> {
  const response = await client.get<Alert[]>("/alerts");
  return response.data;
}

export async function markAlertRead(id: string): Promise<Alert> {
  const response = await client.patch<Alert>(`/alerts/${id}/read`);
  return response.data;
}

export default client;
