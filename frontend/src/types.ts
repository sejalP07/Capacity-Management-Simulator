export type NodeStatus = "Active" | "Failed";
export type Priority = "Low" | "Medium" | "High" | "Critical";
export type Algorithm = "Best Fit" | "Least Loaded" | "Weighted Resource Scoring";
export type TrafficPattern = "Low" | "Medium" | "High" | "Spike";

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Cluster {
  id: number;
  name: string;
  region: string;
  description: string;
}

export interface Node {
  id: number;
  cluster_id: number;
  name: string;
  cpu_cores: number;
  memory_gb: number;
  storage_gb: number;
  status: NodeStatus;
}

export interface Workload {
  id: number;
  cluster_id: number;
  name: string;
  cpu_required: number;
  memory_required: number;
  storage_required: number;
  priority: Priority;
}

export interface Simulation {
  id: number;
  cluster_id: number;
  algorithm: Algorithm;
  traffic_pattern: TrafficPattern;
  duration_hours: number;
  results: {
    timeline: Array<{ timestamp: string; cpu: number; memory: number; storage: number; traffic_multiplier: number }>;
    peak_utilization: Record<string, number>;
    bottlenecks: string[];
    placement: {
      utilization: Record<string, number>;
      nodes: Array<Record<string, unknown>>;
      unplaced_workloads: Array<{ id: number; name: string }>;
    };
  };
  created_at: string;
}

export interface Dashboard {
  total_clusters: number;
  active_nodes: number;
  active_workloads: number;
  utilization: Record<"cpu" | "memory" | "storage", number>;
  health: string;
  recent_simulations: Simulation[];
}

export interface Forecast {
  cluster_id: number;
  exhaustion_dates: Record<string, string>;
  future_needs: Record<string, number>;
  recommendations: string[];
}
