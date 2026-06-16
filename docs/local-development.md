# Local Development

Use Docker Compose for the closest match to the production-style stack.

```bash
cp .env.example .env
docker compose up --build
```

Open the frontend at `http://localhost:5173` and the FastAPI docs at `http://localhost:8000/docs`.

For manual development, run the backend and frontend in separate terminals.

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt
./.venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
