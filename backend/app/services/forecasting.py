from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Cluster, Simulation


def forecast_capacity(cluster: Cluster, simulations: list[Simulation]) -> dict:
    latest = simulations[-1].results if simulations else synthetic_baseline(cluster)
    timeline = latest.get("timeline", [])
    resources = ("cpu", "memory", "storage")
    exhaustion_dates = {}
    future_needs = {}
    recommendations = []

    for resource in resources:
        values = [point[resource] for point in timeline] or [latest.get("placement", {}).get("utilization", {}).get(resource, 0)]
        current = values[-1] if values else 0
        growth_per_day = max(0.4, estimate_growth(values))
        days_to_exhaustion = max(0, int((90 - current) / growth_per_day)) if current < 90 else 0
        exhaustion_dates[resource] = (datetime.utcnow() + timedelta(days=days_to_exhaustion)).date().isoformat()
        future_needs[resource] = round(max(0, current + growth_per_day * 30 - 70), 2)
        if days_to_exhaustion <= 30:
            recommendations.append(f"Add {resource} capacity within {days_to_exhaustion} days")

    if not recommendations:
        recommendations.append("No immediate scaling action required; continue weekly simulations")

    return {
        "cluster_id": cluster.id,
        "exhaustion_dates": exhaustion_dates,
        "future_needs": future_needs,
        "recommendations": recommendations,
    }


def estimate_growth(values: list[float]) -> float:
    if len(values) < 2:
        return 0.6
    return round(max(0.2, (values[-1] - values[0]) / max(1, len(values) / 24)), 2)


def synthetic_baseline(cluster: Cluster) -> dict:
    node_count = max(1, len(cluster.nodes))
    workload_count = len(cluster.workloads)
    baseline = min(88, workload_count * 12 / node_count)
    return {"placement": {"utilization": {"cpu": baseline, "memory": baseline * 0.85, "storage": baseline * 0.65}}}
