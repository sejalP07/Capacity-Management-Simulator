from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from authlib.integrations.starlette_client import OAuth

from app.auth import create_access_token, get_current_user, get_or_create_user
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Cluster, Node, Priority, Simulation, User, Workload
from app.schemas import (
    ClusterCreate,
    ClusterRead,
    DashboardRead,
    FailoverRun,
    ForecastRead,
    NodeCreate,
    NodeRead,
    SimulationRead,
    SimulationRun,
    Token,
    UserRead,
    WorkloadCreate,
    WorkloadRead,
)
from app.services.forecasting import forecast_capacity
from app.services.reports import csv_report, json_report, pdf_report
from app.services.simulation import run_failover, run_simulation


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Capacity Management Simulator API", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth = OAuth()
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
if settings.github_client_id and settings.github_client_secret:
    oauth.register(
        name="github",
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/demo-login", response_model=Token)
def demo_login(db: Session = Depends(get_db)) -> Token:
    user = get_or_create_user(db, email="sre@example.com", name="Demo SRE", provider="demo")
    seed_demo_data(db, user)
    return Token(access_token=create_access_token(user), user=UserRead.model_validate(user))


@app.get("/api/auth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    if provider not in {"google", "github"} or not getattr(oauth, provider, None):
        raise HTTPException(status_code=400, detail=f"{provider.title()} OAuth is not configured")
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/{provider}/callback"
    return await getattr(oauth, provider).authorize_redirect(request, redirect_uri)


@app.get("/api/auth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider == "google" and getattr(oauth, "google", None):
        token = await oauth.google.authorize_access_token(request)
        profile = token.get("userinfo") or await oauth.google.parse_id_token(request, token)
        email = profile["email"]
        name = profile.get("name", email.split("@")[0])
    elif provider == "github" and getattr(oauth, "github", None):
        token = await oauth.github.authorize_access_token(request)
        profile = (await oauth.github.get("user", token=token)).json()
        emails = (await oauth.github.get("user/emails", token=token)).json()
        primary = next((item for item in emails if item.get("primary")), emails[0])
        email = primary["email"]
        name = profile.get("name") or profile.get("login") or email.split("@")[0]
    else:
        raise HTTPException(status_code=400, detail=f"{provider.title()} OAuth is not configured")

    user = get_or_create_user(db, email=email, name=name, provider=provider)
    access_token = create_access_token(user)
    return RedirectResponse(f"{settings.frontend_url}/auth/callback?token={access_token}")


@app.get("/api/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@app.get("/api/dashboard", response_model=DashboardRead)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clusters = owned_clusters(db, user)
    cluster_ids = [cluster.id for cluster in clusters]
    nodes = db.query(Node).filter(Node.cluster_id.in_(cluster_ids)).all() if cluster_ids else []
    workloads = db.query(Workload).filter(Workload.cluster_id.in_(cluster_ids)).all() if cluster_ids else []
    simulations = (
        db.query(Simulation).filter(Simulation.cluster_id.in_(cluster_ids)).order_by(Simulation.created_at.desc()).limit(5).all()
        if cluster_ids
        else []
    )
    utilization = aggregate_dashboard_utilization(nodes, workloads)
    health = "Healthy"
    if any(value >= 85 for value in utilization.values()):
        health = "At Risk"
    if not nodes:
        health = "Needs Setup"
    return {
        "total_clusters": len(clusters),
        "active_nodes": len([node for node in nodes if node.status.value == "Active"]),
        "active_workloads": len(workloads),
        "utilization": utilization,
        "health": health,
        "recent_simulations": simulations,
    }


@app.get("/api/clusters", response_model=list[ClusterRead])
def list_clusters(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return owned_clusters(db, user)


@app.post("/api/clusters", response_model=ClusterRead)
def create_cluster(payload: ClusterCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = Cluster(user_id=user.id, **payload.model_dump())
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


@app.put("/api/clusters/{cluster_id}", response_model=ClusterRead)
def update_cluster(cluster_id: int, payload: ClusterCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = get_cluster(db, user, cluster_id)
    for key, value in payload.model_dump().items():
        setattr(cluster, key, value)
    db.commit()
    db.refresh(cluster)
    return cluster


@app.delete("/api/clusters/{cluster_id}", status_code=204)
def delete_cluster(cluster_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_cluster(db, user, cluster_id))
    db.commit()
    return Response(status_code=204)


@app.get("/api/nodes", response_model=list[NodeRead])
def list_nodes(cluster_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Node).join(Cluster).filter(Cluster.user_id == user.id)
    if cluster_id:
        query = query.filter(Node.cluster_id == cluster_id)
    return query.all()


@app.post("/api/nodes", response_model=NodeRead)
def create_node(payload: NodeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_cluster(db, user, payload.cluster_id)
    node = Node(**payload.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@app.put("/api/nodes/{node_id}", response_model=NodeRead)
def update_node(node_id: int, payload: NodeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    node = get_node(db, user, node_id)
    get_cluster(db, user, payload.cluster_id)
    for key, value in payload.model_dump().items():
        setattr(node, key, value)
    db.commit()
    db.refresh(node)
    return node


@app.delete("/api/nodes/{node_id}", status_code=204)
def delete_node(node_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_node(db, user, node_id))
    db.commit()
    return Response(status_code=204)


@app.get("/api/workloads", response_model=list[WorkloadRead])
def list_workloads(cluster_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Workload).join(Cluster).filter(Cluster.user_id == user.id)
    if cluster_id:
        query = query.filter(Workload.cluster_id == cluster_id)
    return query.all()


@app.post("/api/workloads", response_model=WorkloadRead)
def create_workload(payload: WorkloadCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_cluster(db, user, payload.cluster_id)
    workload = Workload(**payload.model_dump())
    db.add(workload)
    db.commit()
    db.refresh(workload)
    return workload


@app.put("/api/workloads/{workload_id}", response_model=WorkloadRead)
def update_workload(workload_id: int, payload: WorkloadCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workload = get_workload(db, user, workload_id)
    get_cluster(db, user, payload.cluster_id)
    for key, value in payload.model_dump().items():
        setattr(workload, key, value)
    db.commit()
    db.refresh(workload)
    return workload


@app.delete("/api/workloads/{workload_id}", status_code=204)
def delete_workload(workload_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_workload(db, user, workload_id))
    db.commit()
    return Response(status_code=204)


@app.post("/api/simulations/run", response_model=SimulationRead)
def create_simulation(payload: SimulationRun, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = get_cluster(db, user, payload.cluster_id)
    return run_simulation(db, cluster, payload.algorithm, payload.traffic_pattern, payload.duration_hours)


@app.get("/api/simulations", response_model=list[SimulationRead])
def list_simulations(cluster_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Simulation).join(Cluster).filter(Cluster.user_id == user.id)
    if cluster_id:
        query = query.filter(Simulation.cluster_id == cluster_id)
    return query.order_by(Simulation.created_at.desc()).all()


@app.post("/api/failover")
def failover(payload: FailoverRun, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = get_cluster(db, user, payload.cluster_id)
    return run_failover(cluster, payload.failed_node_ids, payload.algorithm)


@app.get("/api/forecast/{cluster_id}", response_model=ForecastRead)
def forecast(cluster_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = get_cluster(db, user, cluster_id)
    simulations = db.query(Simulation).filter(Simulation.cluster_id == cluster.id).order_by(Simulation.created_at.asc()).all()
    return forecast_capacity(cluster, simulations)


@app.get("/api/reports/{simulation_id}")
def report(
    simulation_id: int,
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    simulation = db.query(Simulation).join(Cluster).filter(Simulation.id == simulation_id, Cluster.user_id == user.id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if format == "csv":
        return Response(csv_report(simulation), media_type="text/csv", headers=download_headers(simulation_id, "csv"))
    if format == "pdf":
        return Response(pdf_report(simulation), media_type="application/pdf", headers=download_headers(simulation_id, "pdf"))
    return Response(json_report(simulation), media_type="application/json", headers=download_headers(simulation_id, "json"))


def owned_clusters(db: Session, user: User) -> list[Cluster]:
    return db.query(Cluster).filter(Cluster.user_id == user.id).order_by(Cluster.id.asc()).all()


def get_cluster(db: Session, user: User, cluster_id: int) -> Cluster:
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id, Cluster.user_id == user.id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


def get_node(db: Session, user: User, node_id: int) -> Node:
    node = db.query(Node).join(Cluster).filter(Node.id == node_id, Cluster.user_id == user.id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


def get_workload(db: Session, user: User, workload_id: int) -> Workload:
    workload = db.query(Workload).join(Cluster).filter(Workload.id == workload_id, Cluster.user_id == user.id).first()
    if not workload:
        raise HTTPException(status_code=404, detail="Workload not found")
    return workload


def aggregate_dashboard_utilization(nodes: list[Node], workloads: list[Workload]) -> dict[str, float]:
    active_nodes = [node for node in nodes if node.status.value == "Active"]
    totals = {
        "cpu": sum(node.cpu_cores for node in active_nodes),
        "memory": sum(node.memory_gb for node in active_nodes),
        "storage": sum(node.storage_gb for node in active_nodes),
    }
    used = {
        "cpu": sum(workload.cpu_required for workload in workloads),
        "memory": sum(workload.memory_required for workload in workloads),
        "storage": sum(workload.storage_required for workload in workloads),
    }
    return {key: round((used[key] / totals[key]) * 100, 2) if totals[key] else 0 for key in totals}


def download_headers(simulation_id: int, extension: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="simulation-{simulation_id}.{extension}"'}


def seed_demo_data(db: Session, user: User) -> None:
    if db.query(Cluster).filter(Cluster.user_id == user.id).first():
        return
    cluster = Cluster(user_id=user.id, name="Production East", region="us-east-1", description="Primary SaaS workload cluster")
    db.add(cluster)
    db.flush()
    db.add_all(
        [
            Node(cluster_id=cluster.id, name="node-a", cpu_cores=32, memory_gb=128, storage_gb=1200),
            Node(cluster_id=cluster.id, name="node-b", cpu_cores=24, memory_gb=96, storage_gb=900),
            Node(cluster_id=cluster.id, name="node-c", cpu_cores=16, memory_gb=64, storage_gb=700),
        ]
    )
    db.add_all(
        [
            Workload(cluster_id=cluster.id, name="api-gateway", cpu_required=8, memory_required=20, storage_required=80, priority=Priority.critical),
            Workload(cluster_id=cluster.id, name="checkout", cpu_required=10, memory_required=28, storage_required=120, priority=Priority.high),
            Workload(cluster_id=cluster.id, name="analytics", cpu_required=12, memory_required=36, storage_required=240, priority=Priority.medium),
            Workload(cluster_id=cluster.id, name="batch-worker", cpu_required=6, memory_required=18, storage_required=160, priority=Priority.low),
        ]
    )
    db.commit()
