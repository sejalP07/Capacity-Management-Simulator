from types import SimpleNamespace

from app.models import NodeStatus, Priority
from app.services.placement import place_workloads


def node(node_id, cpu=16, memory=64, storage=500, status=NodeStatus.active):
    return SimpleNamespace(
        id=node_id,
        name=f"node-{node_id}",
        cpu_cores=cpu,
        memory_gb=memory,
        storage_gb=storage,
        status=status,
    )


def workload(workload_id, cpu=4, memory=8, storage=50, priority=Priority.medium):
    return SimpleNamespace(
        id=workload_id,
        name=f"workload-{workload_id}",
        cpu_required=cpu,
        memory_required=memory,
        storage_required=storage,
        priority=priority,
    )


def test_best_fit_places_workload_on_active_node():
    result = place_workloads([node(1), node(2)], [workload(1)], "Best Fit")

    assert result["unplaced_workloads"] == []
    assert sum(len(item["workloads"]) for item in result["nodes"]) == 1


def test_failed_nodes_are_excluded_from_placement():
    result = place_workloads([node(1, status=NodeStatus.failed), node(2)], [workload(1)], "Least Loaded")

    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["node_id"] == 2


def test_unplaced_workload_is_reported_when_capacity_is_insufficient():
    result = place_workloads([node(1, cpu=2, memory=2, storage=10)], [workload(1, cpu=8, memory=16, storage=40)], "Weighted Resource Scoring")

    assert result["unplaced_workloads"] == [{"id": 1, "name": "workload-1"}]
