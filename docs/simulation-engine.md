# Simulation Engine

The placement engine supports three algorithms:

- Best Fit
- Least Loaded
- Weighted Resource Scoring

Traffic patterns apply multipliers to workload requirements over the requested duration:

- Low
- Medium
- High
- Spike

Simulation output includes placement, hourly utilization timeline, peak utilization, and bottleneck findings.

Failover simulation marks selected nodes as failed, reruns placement on the remaining active nodes, and reports recovery time, availability impact, and cluster health.
