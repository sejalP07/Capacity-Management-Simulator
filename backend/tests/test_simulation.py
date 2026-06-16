from types import SimpleNamespace

from app.models import NodeStatus, Priority
from app.services.simulation import build_simulation_results, run_failover


def node(node_id, status=NodeStatus.active):
    return SimpleNamespace(
        id=node_id,
        name=f"node-{node_id}",
        cpu_cores=16,
        memory_gb=64,
        storage_gb=500,
        status=status,
    )


def workload(workload_id):
    return SimpleNamespace(
        id=workload_id,
        name=f"workload-{workload_id}",
        cpu_required=4,
        memory_required=8,
        storage_required=50,
        priority=Priority.high,
    )


def test_simulation_builds_timeline_for_requested_duration():
    result = build_simulation_results([node(1), node(2)], [workload(1)], "Best Fit", "Medium", 6)

    assert len(result["timeline"]) == 6
    assert "peak_utilization" in result
    assert result["placement"]["unplaced_workloads"] == []


def test_failover_reports_degraded_health_when_capacity_is_lost():
    cluster = SimpleNamespace(nodes=[node(1), node(2)], workloads=[workload(1), workload(2)])

    result = run_failover(cluster, [1], "Least Loaded")

    assert result["failed_node_ids"] == [1]
    assert result["availability_impact_percent"] > 0
    assert result["cluster_health"] in {"Recovered", "Degraded", "Critical"}
