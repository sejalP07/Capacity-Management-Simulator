# Capacity Management Simulator

A full-stack web application for DevOps Engineers and SREs to model cluster capacity, place workloads, run traffic and failover simulations, forecast exhaustion, and export reports.

## Stack

- Frontend: React, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis
- Auth: Google and GitHub OAuth entry points with JWT sessions
- Deployment: Docker and Docker Compose

## Quick Start

1. Copy environment defaults:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

For local backend development without OAuth credentials, use `POST /api/auth/demo-login` or the demo login button in the UI.

## Project Layout

```text
backend/      FastAPI app, SQLAlchemy models, scheduling and simulation services
frontend/     React dashboard app
docker-compose.yml
```

## Core Simulator Logic

The scheduling engine supports:

- Best Fit
- Least Loaded
- Weighted Resource Scoring

Simulation supports:

- Low, Medium, High, and Spike traffic patterns
- Node failover and workload redistribution
- Capacity forecasting based on historical simulation points
- PDF, CSV, and JSON report exports
