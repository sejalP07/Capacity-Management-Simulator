# Docker Setup

The Docker Compose stack starts four services:

- `postgres` for persistent relational data
- `redis` for simulation result caching
- `backend` for FastAPI
- `frontend` for the Vite React app

Useful commands:

```bash
docker compose up --build
docker compose down
docker compose logs -f backend
docker compose logs -f frontend
```

Use `docker compose down -v` only when you want to delete the PostgreSQL volume and start with an empty database.
