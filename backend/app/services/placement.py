from __future__ import annotations

from dataclasses import dataclass, field

from app.models import Node, NodeStatus, Workload


PRIORITY_WEIGHT = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}


@dataclass
class NodeState:
    node: Node
    used_cpu: float = 0
    used_memory: float = 0
    used_storage: float = 0
    workloads: list[Workload] = field(default_factory=list)

    @property
    def cpu_utilization(self) -> float:
        return percent(self.used_cpu, self.node.cpu_cores)

    @property
    def memory_utilization(self) -> float:
        return percent(self.used_memory, self.node.memory_gb)

    @property
    def storage_utilization(self) -> float:
        return percent(self.used_storage, self.node.storage_gb)

    @property
    def average_utilization(self) -> float:
        return (self.cpu_utilization + self.memory_utilization + self.storage_utilization) / 3

    def fits(self, workload: Workload, multiplier: float = 1.0) -> bool:
        return (
            self.used_cpu + workload.cpu_required * multiplier <= self.node.cpu_cores
            and self.used_memory + workload.memory_required * multiplier <= self.node.memory_gb
            and self.used_storage + workload.storage_required * multiplier <= self.node.storage_gb
        )

    def assign(self, workload: Workload, multiplier: float = 1.0) -> None:
        self.used_cpu += workload.cpu_required * multiplier
        self.used_memory += workload.memory_required * multiplier
        self.used_storage += workload.storage_required * multiplier
        self.workloads.append(workload)


def percent(used: float, total: float) -> float:
    return round((used / total) * 100, 2) if total else 0


def place_workloads(nodes: list[Node], workloads: list[Workload], algorithm: str, multiplier: float = 1.0) -> dict:
    states = [NodeState(node=node) for node in nodes if node.status == NodeStatus.active]
    ordered_workloads = sorted(
        workloads,
        key=lambda item: (PRIORITY_WEIGHT.get(item.priority.value, 1), item.cpu_required + item.memory_required),
        reverse=True,
    )
    unplaced = []

    for workload in ordered_workloads:
        candidates = [state for state in states if state.fits(workload, multiplier)]
        if not candidates:
            unplaced.append(workload)
            continue

        if algorithm == "Best Fit":
            target = min(candidates, key=lambda state: remaining_capacity_score(state, workload, multiplier))
        elif algorithm == "Least Loaded":
            target = min(candidates, key=lambda state: state.average_utilization)
        else:
            target = max(candidates, key=lambda state: weighted_score(state, workload, multiplier))
        target.assign(workload, multiplier)

    node_results = []
    for state in states:
        node_results.append(
            {
                "node_id": state.node.id,
                "node_name": state.node.name,
                "cpu_utilization": state.cpu_utilization,
                "memory_utilization": state.memory_utilization,
                "storage_utilization": state.storage_utilization,
                "average_utilization": round(state.average_utilization, 2),
                "workloads": [{"id": workload.id, "name": workload.name, "priority": workload.priority.value} for workload in state.workloads],
            }
        )

    totals = aggregate_totals(states)
    return {
        "algorithm": algorithm,
        "nodes": node_results,
        "unplaced_workloads": [{"id": workload.id, "name": workload.name} for workload in unplaced],
        "utilization": totals,
        "bottlenecks": bottlenecks(node_results, unplaced),
    }


def remaining_capacity_score(state: NodeState, workload: Workload, multiplier: float) -> float:
    return (
        state.node.cpu_cores - state.used_cpu - workload.cpu_required * multiplier
        + state.node.memory_gb - state.used_memory - workload.memory_required * multiplier
        + state.node.storage_gb - state.used_storage - workload.storage_required * multiplier
    )


def weighted_score(state: NodeState, workload: Workload, multiplier: float) -> float:
    cpu_headroom = 1 - ((state.used_cpu + workload.cpu_required * multiplier) / state.node.cpu_cores)
    memory_headroom = 1 - ((state.used_memory + workload.memory_required * multiplier) / state.node.memory_gb)
    storage_headroom = 1 - ((state.used_storage + workload.storage_required * multiplier) / state.node.storage_gb)
    balance_penalty = abs(cpu_headroom - memory_headroom) + abs(memory_headroom - storage_headroom)
    return cpu_headroom * 0.45 + memory_headroom * 0.35 + storage_headroom * 0.2 - balance_penalty * 0.15


def aggregate_totals(states: list[NodeState]) -> dict[str, float]:
    total_cpu = sum(state.node.cpu_cores for state in states)
    total_memory = sum(state.node.memory_gb for state in states)
    total_storage = sum(state.node.storage_gb for state in states)
    used_cpu = sum(state.used_cpu for state in states)
    used_memory = sum(state.used_memory for state in states)
    used_storage = sum(state.used_storage for state in states)
    return {
        "cpu": percent(used_cpu, total_cpu),
        "memory": percent(used_memory, total_memory),
        "storage": percent(used_storage, total_storage),
    }


def bottlenecks(node_results: list[dict], unplaced: list[Workload]) -> list[str]:
    findings = []
    if unplaced:
        findings.append(f"{len(unplaced)} workload(s) could not be placed")
    for resource in ("cpu", "memory", "storage"):
        hot_nodes = [node["node_name"] for node in node_results if node[f"{resource}_utilization"] >= 85]
        if hot_nodes:
            findings.append(f"{resource.upper()} pressure on {', '.join(hot_nodes)}")
    return findings or ["No critical bottlenecks detected"]
