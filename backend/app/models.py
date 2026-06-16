from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NodeStatus(str, Enum):
    active = "Active"
    failed = "Failed"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="demo")

    clusters: Mapped[list["Cluster"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    region: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500), default="")

    user: Mapped[User] = relationship(back_populates="clusters")
    nodes: Mapped[list["Node"]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    workloads: Mapped[list["Workload"]] = relationship(back_populates="cluster", cascade="all, delete-orphan")
    simulations: Mapped[list["Simulation"]] = relationship(back_populates="cluster", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    cpu_cores: Mapped[float] = mapped_column(Float)
    memory_gb: Mapped[float] = mapped_column(Float)
    storage_gb: Mapped[float] = mapped_column(Float)
    status: Mapped[NodeStatus] = mapped_column(SAEnum(NodeStatus), default=NodeStatus.active)

    cluster: Mapped[Cluster] = relationship(back_populates="nodes")


class Workload(Base):
    __tablename__ = "workloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    cpu_required: Mapped[float] = mapped_column(Float)
    memory_required: Mapped[float] = mapped_column(Float)
    storage_required: Mapped[float] = mapped_column(Float)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)

    cluster: Mapped[Cluster] = relationship(back_populates="workloads")


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), index=True)
    algorithm: Mapped[str] = mapped_column(String(80))
    traffic_pattern: Mapped[str] = mapped_column(String(80), default="Medium")
    duration_hours: Mapped[int] = mapped_column(Integer, default=24)
    results: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cluster: Mapped[Cluster] = relationship(back_populates="simulations")
