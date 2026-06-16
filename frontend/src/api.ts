import type { Algorithm, Cluster, Dashboard, Forecast, Node, Simulation, TrafficPattern, Workload } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
const TOKEN_KEY = "capacity-sim-token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });
  if (!response.ok) {
    throw new Error((await response.json().catch(() => null))?.detail ?? "Request failed");
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  authUrl: (provider: "google" | "github") => `${API_URL}/auth/${provider}/login`,
  downloadReport: async (id: number, format: "json" | "csv" | "pdf") => {
    const token = getToken();
    const response = await fetch(`${API_URL}/reports/${id}?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    if (!response.ok) throw new Error("Report download failed");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `simulation-${id}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  },
  demoLogin: () => request<{ access_token: string }>("/auth/demo-login", { method: "POST" }),
  dashboard: () => request<Dashboard>("/dashboard"),
  clusters: () => request<Cluster[]>("/clusters"),
  createCluster: (payload: Omit<Cluster, "id">) => request<Cluster>("/clusters", { method: "POST", body: JSON.stringify(payload) }),
  deleteCluster: (id: number) => request<void>(`/clusters/${id}`, { method: "DELETE" }),
  nodes: (clusterId?: number) => request<Node[]>(`/nodes${clusterId ? `?cluster_id=${clusterId}` : ""}`),
  createNode: (payload: Omit<Node, "id">) => request<Node>("/nodes", { method: "POST", body: JSON.stringify(payload) }),
  deleteNode: (id: number) => request<void>(`/nodes/${id}`, { method: "DELETE" }),
  workloads: (clusterId?: number) => request<Workload[]>(`/workloads${clusterId ? `?cluster_id=${clusterId}` : ""}`),
  createWorkload: (payload: Omit<Workload, "id">) => request<Workload>("/workloads", { method: "POST", body: JSON.stringify(payload) }),
  deleteWorkload: (id: number) => request<void>(`/workloads/${id}`, { method: "DELETE" }),
  simulations: (clusterId?: number) => request<Simulation[]>(`/simulations${clusterId ? `?cluster_id=${clusterId}` : ""}`),
  runSimulation: (payload: { cluster_id: number; algorithm: Algorithm; traffic_pattern: TrafficPattern; duration_hours: number }) =>
    request<Simulation>("/simulations/run", { method: "POST", body: JSON.stringify(payload) }),
  failover: (payload: { cluster_id: number; failed_node_ids: number[]; algorithm: Algorithm }) =>
    request<Record<string, unknown>>("/failover", { method: "POST", body: JSON.stringify(payload) }),
  forecast: (clusterId: number) => request<Forecast>(`/forecast/${clusterId}`)
};
