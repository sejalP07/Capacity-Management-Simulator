# Capacity Management Simulator

**A Distributed Infrastructure Capacity Planning and Resource Management System**

The Capacity Management Simulator is a Python-based project designed to simulate resource allocation across distributed database clusters. It helps evaluate infrastructure capacity, distribute workloads across nodes, identify resource bottlenecks, and explore scaling and recovery strategies under changing workloads.

The system focuses on efficient resource utilization, workload scheduling, capacity planning, and infrastructure resilience.

## 🚀 Key Features

- **Resource-Aware Workload Scheduling:** Allocate workloads based on CPU, memory, and storage utilization.
- **Distributed Resource Allocation:** Simulate workload placement across multiple database nodes.
- **Scheduling Algorithms:** Support strategies such as Round Robin, Least Loaded, and Bin Packing for comparing allocation decisions.
- **Capacity Monitoring:** Track resource utilization and node-level capacity metrics.
- **Capacity Forecasting:** Estimate future resource requirements based on workload trends.
- **Threshold-Based Scaling:** Generate scaling recommendations when resource utilization exceeds configured thresholds.
- **Failure and Recovery Simulation:** Model node failures, recovery, and workload redistribution.
- **Redis-Based Processing:** Use Redis for caching, transient state, or asynchronous processing where configured.
- **Persistent Storage:** Use PostgreSQL to store cluster configurations, workloads, resource metrics, and simulation results.
- **Containerized Deployment:** Use Docker to package and run the application and its supporting services.

## 🏗️ System Architecture

The system follows a modular architecture that separates workload simulation, resource scheduling, metric processing, and data persistence.

```text
          Workload Generator
                  |
                  v
       Capacity Simulation Engine
                  |
                  v
        Resource Scheduling
                  |
                  v
       Cluster and Node Manager
                  |
          +-------+-------+
          |               |
          v               v
    Redis Layer      PostgreSQL
          |               |
          +-------+-------+
                  |
                  v
        Monitoring & Analytics
                  |
                  v
       Capacity and Scaling Insights
```

**Component responsibilities**

| Component | Responsibility |
|---|---|
| Workload Generator | Creates simulated workloads and demand patterns. |
| Scheduling Engine | Selects nodes for workload placement. |
| Cluster Manager | Tracks node capacity, utilization, and availability. |
| Redis | Supports caching or transient data processing. |
| PostgreSQL | Persists application and simulation data. |
| Monitoring Module | Aggregates metrics and identifies capacity issues. |
| Scaling Module | Evaluates utilization thresholds and suggests capacity changes. |

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Simulation logic and resource scheduling |
| FastAPI | REST API layer, where implemented |
| PostgreSQL | Persistent data storage |
| Redis | Caching and transient processing |
| Docker | Containerization and environment consistency |
| Pytest | Automated testing, where configured |

## ⚙️ Resource Scheduling Strategies

The simulator can evaluate different resource placement strategies to understand their effect on resource utilization and workload distribution.

### 1. Round Robin
Distributes workloads across available nodes in sequence. Useful as a baseline for comparing allocation strategies.

### 2. Least Loaded
Selects an eligible node with the lowest current load, helping avoid concentrating workloads on already busy nodes.

### 3. Bin Packing
Attempts to consolidate workloads onto fewer suitable nodes while respecting resource capacity constraints, potentially improving utilization.

### Resource Constraints

Each node can be evaluated against resource dimensions such as:

- CPU utilization and available processing capacity
- Memory consumption and available memory
- Storage usage and remaining capacity
- Node availability and workload limits

The scheduling engine should reject placements that exceed configured resource limits and consider redistribution when nodes become unavailable.

## 📊 Capacity Planning and Monitoring

The simulator can be used to explore how infrastructure responds to changing workload demand.

Key metrics include:

- CPU, memory, and storage utilization
- Available capacity per node
- Workload distribution across the cluster
- Capacity threshold violations
- Failed or rejected workload placements
- Resource availability following node recovery
- Projected resource demand and scaling recommendations

These metrics help compare scheduling strategies and identify potential capacity bottlenecks before applying similar decisions to real infrastructure.

## 🔄 Failure and Recovery Workflow

1. Simulate a node failure.
2. Identify workloads affected by the failure.
3. Recalculate available cluster capacity.
4. Attempt to redistribute eligible workloads to healthy nodes.
5. Record the resulting allocation and resource utilization.
6. Evaluate whether additional capacity is required.

This workflow is intended to explore resilience and recovery behavior in a controlled simulation environment.

## 📁 Project Structure

A possible organization for the project is shown below. Adjust it to match the files in your actual repository.

```text
Capacity-Management-Simulator/
├── app/
│   ├── main.py
│   ├── api/
│   ├── simulation/
│   ├── scheduling/
│   ├── cluster/
│   ├── monitoring/
│   ├── forecasting/
│   ├── database/
│   └── models/
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 💻 Getting Started

### Prerequisites

Install the following tools before running the project:

- Python 3.10 or later
- PostgreSQL
- Redis
- Docker and Docker Compose, if using containerized deployment
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/sejalP07/Capacity-Management-Simulator.git
cd Capacity-Management-Simulator
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on the configuration supported by your application.

Example configuration:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/capacity_db
REDIS_URL=redis://localhost:6379/0
```

Replace the example credentials with your local configuration. Do not commit actual secrets to GitHub.

### 5. Start the Application

If the FastAPI entry point is `app/main.py` and exposes an `app` instance, run:

```bash
uvicorn app.main:app --reload
```

Open the API documentation at:

```text
http://127.0.0.1:8000/docs
```

If your project uses a different entry point or does not expose FastAPI endpoints, update this command accordingly.

### 6. Run with Docker

If the repository includes a working Docker Compose configuration, start the configured services using:

```bash
docker compose up --build
```

Stop the services with:

```bash
docker compose down
```

### 7. Run Tests

If the project includes a Pytest test suite, run:

```bash
pytest -v
```

## 🧪 Example Simulation Scenario

Consider a cluster containing multiple database nodes, each with different CPU, memory, and storage capacities.

A workload arrives with specific resource requirements. The simulator evaluates eligible nodes, applies the selected scheduling strategy, and records the resulting allocation.

You can then introduce additional workloads, increase demand, or simulate a node failure to observe how resource availability and workload distribution change.

**Expected evaluation areas:**

- Whether workloads fit within node capacity
- How evenly workloads are distributed
- Which nodes approach configured utilization limits
- How much capacity remains available
- Whether workloads can be redistributed after a failure

## 🎯 Project Objectives

- Understand resource scheduling in distributed infrastructure.
- Compare workload allocation strategies under different demand patterns.
- Explore capacity constraints and infrastructure bottlenecks.
- Evaluate scaling recommendations and recovery scenarios.
- Apply backend engineering and data persistence concepts to infrastructure simulation.

## 🔮 Future Enhancements

- Interactive cluster visualization and monitoring dashboard.
- More advanced demand forecasting using historical workload data.
- Dynamic scaling policies based on multiple resource metrics.
- Concurrent workload simulation and stress testing.
- Improved scheduling using weighted resource utilization.
- Detailed simulation reports comparing scheduling strategies.
- Integration with cloud monitoring platforms and infrastructure APIs.

## 👩‍💻 Author

**Sejal P.**

GitHub: [@sejalP07](https://github.com/sejalP07)

Project Repository: [Capacity Management Simulator](https://github.com/sejalP07/Capacity-Management-Simulator)

---

*This project explores distributed capacity planning, resource scheduling, and infrastructure resilience through simulation.*
