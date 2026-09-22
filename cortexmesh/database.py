"""
CortexMesh — SQLAlchemy database layer.

Uses SQLite by default, PostgreSQL-ready via DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, create_engine, event
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./cortexmesh.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class NodeModel(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True)
    hostname = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    platform = Column(String, nullable=False)
    architecture = Column(String, nullable=False)
    agent_version = Column(String, nullable=False)
    roles = Column(JSON, default=list)
    state = Column(String, default="online")
    capabilities = Column(JSON, default=dict)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)
    compute_enabled = Column(Boolean, default=True)
    security_state = Column(String, default="active")


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    task_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    state = Column(String, default="queued")
    priority = Column(String, default="normal")
    node_id = Column(String, ForeignKey("nodes.id"), nullable=True)
    requirements = Column(JSON, default=dict)
    payload = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    scheduler_explanation = Column(Text, nullable=True)
    timeout_seconds = Column(Integer, default=3600)
    max_retries = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    idempotency_key = Column(String, nullable=True, unique=True)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResourceLeaseModel(Base):
    __tablename__ = "resource_leases"

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    node_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    cpu_threads = Column(Integer, nullable=True)
    memory_bytes = Column(Integer, nullable=True)
    vram_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    released_at = Column(DateTime, nullable=True)


class ProviderModel(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True)
    provider_type = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_available = Column(Boolean, default=False)
    models = Column(JSON, default=list)
    extra_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    source_node_id = Column(String, nullable=True)
    source_task_id = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EnrollmentTokenModel(Base):
    __tablename__ = "enrollment_tokens"

    id = Column(String, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by_node_id = Column(String, nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class StorageLocationModel(Base):
    __tablename__ = "storage_locations"

    id = Column(String, primary_key=True)
    node_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    path = Column(String, nullable=False)
    category = Column(String, default="files")
    total_bytes = Column(Integer, default=0)
    used_bytes = Column(Integer, default=0)
    free_bytes = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)


class PolicyModel(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    limit_value = Column(Float, nullable=False)
    policy_type = Column(String, default="soft")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
