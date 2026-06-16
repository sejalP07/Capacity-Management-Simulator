from __future__ import annotations

import json
from datetime import datetime, timedelta

import redis
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Cluster, Node, NodeStatus, Simulation, Workload
from app.services.placement import place_workloads


TRAFFIC_MULTIPLIERS = {
    "Low": [0.45, 0.5, 0.55, 0.6],
    "Medium": [0.75, 0.8, 0.85, 0.9],
    "High": [1.0, 1.1, 1.2, 1.25],
    "Spike": [0.8, 1.0, 1.35, 1.7, 1.25, 0.95],
}


def redis_client():
    try:
        return redis.from_url(get_settings().redis_url, decode_responses=True)
    except redis.RedisError:
        return None


def run_simulation(db: Session, cluster: Cluster, algorithm: str, traffic_pattern: str, duration_hours: int) -> Simulation:
    cache_key = f"simulation:{cluster.id}:{algorithm}:{traffic_pattern}:{duration_hours}:{len(cluster.nodes)}:{len(cluster.workloads)}"
    client = redis_client()
    cached = None
    if client:
        try:
            cached = client.get(cache_key)
        except redis.RedisError:
            cached = None

    if cached:
        results = json.loads(cached)
    else:
        results = build_simulation_results(cluster.nodes, cluster.workloads, algorithm, traffic_pattern, duration_hours)
        if client:
            try:
                client.setex(cache_key, 900, json.dumps(results))
            except redis.RedisError:
                pass

    simulation = Simulation(
        cluster_id=cluster.id,
        algorithm=algorithm,
        traffic_pattern=traffic_pattern,
        duration_hours=duration_hours,
        results=results,
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    return simulation


def build_simulation_results(nodes: list[Node], workloads: list[Workload], algorithm: str, traffic_pattern: str, duration_hours: int) -> dict:
    multipliers = TRAFFIC_MULTIPLIERS[traffic_pattern]
    started_at = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    timeline = []

    for hour in range(duration_hours):
        multiplier = multipliers[hour % len(multipliers)]
        placement = place_workloads(nodes, workloads, algorithm, multiplier)
        utilization = placement["utilization"]
        timeline.append(
            {
                "timestamp": (started_at + timedelta(hours=hour)).isoformat() + "Z",
                "cpu": utilization["cpu"],
                "memory": utilization["memory"],
                "storage": utilization["storage"],
                "traffic_multiplier": multiplier,
            }
        )

    peak = {
        "cpu": max(point["cpu"] for point in timeline) if timeline else 0,
        "memory": max(point["memory"] for point in timeline) if timeline else 0,
        "storage": max(point["storage"] for point in timeline) if timeline else 0,
    }
    return {
        "placement": place_workloads(nodes, workloads, algorithm),
        "timeline": timeline,
        "peak_utilization": peak,
        "bottlenecks": summarize_bottlenecks(timeline),
    }


def run_failover(cluster: Cluster, failed_node_ids: list[int], algorithm: str) -> dict:
    scenario_nodes = []
    for node in cluster.nodes:
        node.status = NodeStatus.failed if node.id in failed_node_ids else node.status
        scenario_nodes.append(node)

    placement = place_workloads(scenario_nodes, cluster.workloads, algorithm)
    lost_capacity = sum(node.cpu_cores + node.memory_gb + node.storage_gb for node in cluster.nodes if node.id in failed_node_ids)
    total_capacity = sum(node.cpu_cores + node.memory_gb + node.storage_gb for node in cluster.nodes)
    availability_impact = round((lost_capacity / total_capacity) * 100, 2) if total_capacity else 0
    recovery_time = min(45, 5 + len(failed_node_ids) * 6 + len(placement["unplaced_workloads"]) * 4)
    health = "Degraded" if placement["unplaced_workloads"] else "Recovered"
    if availability_impact >= 50:
        health = "Critical"

    return {
        "failed_node_ids": failed_node_ids,
        "redistribution": placement,
        "recovery_time_minutes": recovery_time,
        "availability_impact_percent": availability_impact,
        "cluster_health": health,
    }


def summarize_bottlenecks(timeline: list[dict]) -> list[str]:
    findings = []
    for resource in ("cpu", "memory", "storage"):
        peak = max((point[resource] for point in timeline), default=0)
        if peak >= 90:
            findings.append(f"{resource.upper()} exceeds 90% during peak traffic")
        elif peak >= 75:
            findings.append(f"{resource.upper()} should be watched; peak reaches {peak}%")
    return findings or ["Capacity remains within target thresholds"]
