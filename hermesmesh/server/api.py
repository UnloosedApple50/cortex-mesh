"""
HermesMesh — FastAPI Controller API with profiles, policies, and leases.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from hermesmesh.core.leases import LeaseManager, LeaseState
from hermesmesh.core.policies import PolicyEngine, PolicyRule, PolicyType, PolicyAction
from hermesmesh.core.profiles import ProfileManager, ResourceProfile
from hermesmesh.database import (
    AuditLogModel, EnrollmentTokenModel, EventModel, NodeModel,
    PolicyModel, ProviderModel, ResourceLeaseModel, StorageLocationModel,
    TaskModel, async_session, init_db,
)
from hermesmesh.models import (
    EnrollmentToken, ErrorResponse, Event, EventType,
    HealthResponse, NodeRegisterRequest, NodeResponse, NodeRole,
    NodeState, ProviderCreate, ProviderResponse, ResourceLimit,
    StorageLocation, SuccessResponse, TaskResponse, TaskState,
    TaskSubmit, VersionResponse,
)

app = FastAPI(
    title="HermesMesh",
    description="Universal Platform for Multi-Machine Orchestration",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton managers ──────────────────────────────────────────

lease_manager = LeaseManager()
policy_engine = PolicyEngine()
profile_manager = ProfileManager()

# Load default policies
for rule in policy_engine.get_default_policies():
    policy_engine.add_rule(rule)


# ── Health ───────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


@app.get("/api/v1/version", response_model=VersionResponse)
async def version():
    return VersionResponse()


# ── Nodes ────────────────────────────────────────────────────────

@app.get("/api/v1/nodes", response_model=List[NodeResponse])
async def list_nodes():
    async with async_session() as session:
        result = await session.execute(
            __import__("sqlalchemy").select(NodeModel)
        )
        nodes = result.scalars().all()
        return [
            NodeResponse(
                node_id=n.id,
                hostname=n.hostname,
                display_name=n.display_name,
                platform=n.platform,
                architecture=n.architecture,
                agent_version=n.agent_version,
                roles=n.roles or [],
                state=n.state,
                capabilities=n.capabilities or {},
                last_seen=n.last_seen,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in nodes
        ]


@app.get("/api/v1/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: str):
    async with async_session() as session:
        node = await session.get(NodeModel, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        return NodeResponse(
            node_id=node.id,
            hostname=node.hostname,
            display_name=node.display_name,
            platform=node.platform,
            architecture=node.architecture,
            agent_version=node.agent_version,
            roles=node.roles or [],
            state=node.state,
            capabilities=node.capabilities or {},
            last_seen=node.last_seen,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )


@app.post("/api/v1/nodes/register", response_model=NodeResponse)
async def register_node(req: NodeRegisterRequest):
    async with async_session() as session:
        # Validate enrollment token
        from sqlalchemy import select
        token_result = await session.execute(
            select(EnrollmentTokenModel).where(
                EnrollmentTokenModel.token == req.enrollment_token,
                EnrollmentTokenModel.is_used == False,
            )
        )
        token = token_result.scalar_one_or_none()
        if not token:
            raise HTTPException(400, "Invalid or expired enrollment token")
        from datetime import datetime as dt
        now = dt.utcnow() if token.expires_at.tzinfo is None else datetime.now(timezone.utc)
        if token.expires_at < now:
            raise HTTPException(400, "Enrollment token expired")

        # Create node
        node_id = str(uuid.uuid4())
        node = NodeModel(
            id=node_id,
            hostname=req.hostname,
            display_name=req.display_name or req.hostname,
            platform=req.platform.value,
            architecture=req.architecture.value,
            agent_version=req.agent_version,
            roles=[r.value for r in req.roles],
            state=NodeState.ONLINE.value,
            capabilities=req.capabilities.model_dump(),
            last_seen=datetime.now(timezone.utc),
        )
        session.add(node)

        # Mark token as used
        token.is_used = True
        token.used_by_node_id = node_id
        token.used_at = datetime.now(timezone.utc)

        # Create event
        event = EventModel(
            id=str(uuid.uuid4()),
            event_type=EventType.NODE_REGISTERED.value,
            source_node_id=node_id,
            message=f"Node {req.hostname} registered",
        )
        session.add(event)

        # Audit log
        audit = AuditLogModel(
            id=str(uuid.uuid4()),
            actor="system",
            action="node_register",
            target=node_id,
            details={"hostname": req.hostname, "platform": req.platform.value},
        )
        session.add(audit)

        await session.commit()

        # Register node with lease manager
        caps = req.capabilities
        lease_manager.register_node(
            node_id=node_id,
            cpu_threads=caps.cpu.threads or 0,
            memory_bytes=caps.memory.total_bytes,
            vram_bytes=max((g.vram_bytes or 0) for g in caps.gpus) if caps.gpus else 0,
        )

        return NodeResponse(
            node_id=node.id,
            hostname=node.hostname,
            display_name=node.display_name,
            platform=node.platform,
            architecture=node.architecture,
            agent_version=node.agent_version,
            roles=node.roles,
            state=node.state,
            capabilities=node.capabilities,
            last_seen=node.last_seen,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )


@app.post("/api/v1/nodes/{node_id}/heartbeat")
async def node_heartbeat(node_id: str, body: Optional[dict] = None):
    async with async_session() as session:
        node = await session.get(NodeModel, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        node.last_seen = datetime.now(timezone.utc)
        node.state = NodeState.ONLINE.value
        
        # Update metrics if provided
        if body:
            # Store metrics in capabilities JSON for now
            caps = node.capabilities or {}
            caps["last_metrics"] = {
                "cpu_usage_percent": body.get("cpu_usage_percent"),
                "memory_usage_percent": body.get("memory_usage_percent"),
                "gpu_usage_percent": body.get("gpu_usage_percent"),
                "timestamp": body.get("timestamp"),
            }
            node.capabilities = caps
        
        await session.commit()
        return {"status": "ok"}


@app.post("/api/v1/nodes/{node_id}/capabilities")
async def update_capabilities(node_id: str, body: dict):
    """Update node capabilities (for agent capability refresh)."""
    async with async_session() as session:
        node = await session.get(NodeModel, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        node.capabilities = body
        node.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return {"status": "ok"}


@app.patch("/api/v1/nodes/{node_id}")
async def update_node(node_id: str, body: dict):
    """Update node properties (enable/disable)."""
    async with async_session() as session:
        node = await session.get(NodeModel, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        if "compute_enabled" in body:
            node.compute_enabled = bool(body["compute_enabled"])
        if "state" in body:
            node.state = body["state"]
        await session.commit()
        return {"status": "ok", "node_id": node_id}


@app.delete("/api/v1/nodes/{node_id}")
async def delete_node(node_id: str):
    async with async_session() as session:
        node = await session.get(NodeModel, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        await session.delete(node)
        await session.commit()
        return SuccessResponse(message="Node deleted")


# ── Tasks ────────────────────────────────────────────────────────

@app.get("/api/v1/tasks", response_model=List[TaskResponse])
async def list_tasks(state: Optional[str] = None):
    from sqlalchemy import select
    async with async_session() as session:
        query = select(TaskModel)
        if state:
            query = query.where(TaskModel.state == state)
        result = await session.execute(query)
        tasks = result.scalars().all()
        return [
            TaskResponse(
                task_id=t.id,
                task_type=t.task_type,
                title=t.title,
                description=t.description,
                state=t.state,
                priority=t.priority,
                node_id=t.node_id,
                requirements=t.requirements or {},
                payload=t.payload or {},
                result=t.result,
                error=t.error,
                scheduler_explanation=t.scheduler_explanation,
                scheduled_at=t.scheduled_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                created_at=t.created_at,
            )
            for t in tasks
        ]


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def submit_task(task: TaskSubmit):
    from sqlalchemy import select
    async with async_session() as session:
        task_id = str(uuid.uuid4())
        db_task = TaskModel(
            id=task_id,
            task_type=task.task_type.value,
            title=task.title,
            description=task.description,
            state=TaskState.QUEUED.value,
            priority=task.priority.value,
            requirements=task.requirements.model_dump(),
            payload=task.payload,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            idempotency_key=task.idempotency_key,
        )
        session.add(db_task)

        # Create event
        event = EventModel(
            id=str(uuid.uuid4()),
            event_type=EventType.TASK_QUEUED.value,
            source_task_id=task_id,
            message=f"Task queued: {task.title}",
        )
        session.add(event)

        await session.commit()

        return TaskResponse(
            task_id=db_task.id,
            task_type=db_task.task_type,
            title=db_task.title,
            description=db_task.description,
            state=db_task.state,
            priority=db_task.priority,
            requirements=db_task.requirements,
            payload=db_task.payload,
        )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    async with async_session() as session:
        task = await session.get(TaskModel, task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        return TaskResponse(
            task_id=task.id,
            task_type=task.task_type,
            title=task.title,
            description=task.description,
            state=task.state,
            priority=task.priority,
            node_id=task.node_id,
            requirements=task.requirements or {},
            payload=task.payload or {},
            result=task.result,
            error=task.error,
            scheduler_explanation=task.scheduler_explanation,
            scheduled_at=task.scheduled_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )


@app.post("/api/v1/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    async with async_session() as session:
        task = await session.get(TaskModel, task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        if task.state in ("completed", "failed", "cancelled"):
            raise HTTPException(400, f"Cannot cancel task in state {task.state}")
        task.state = TaskState.CANCELLING.value
        await session.commit()
        
        # Release any leases for this task
        lease_manager.release_task_leases(task_id)
        
        return SuccessResponse(message="Cancellation requested")


# ── Profiles ─────────────────────────────────────────────────────

@app.get("/api/v1/profiles")
async def list_profiles():
    """List all resource profiles."""
    return [p.to_dict() for p in profile_manager.list_profiles()]


@app.post("/api/v1/profiles")
async def create_profile(body: dict):
    """Create a new resource profile."""
    profile = profile_manager.create_profile(**body)
    return profile.to_dict()


@app.get("/api/v1/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a profile by ID."""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile.to_dict()


@app.patch("/api/v1/profiles/{profile_id}")
async def update_profile(profile_id: str, body: dict):
    """Update a profile."""
    profile = profile_manager.update_profile(profile_id, **body)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile.to_dict()


@app.delete("/api/v1/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    result = profile_manager.delete_profile(profile_id)
    if not result:
        raise HTTPException(404, "Profile not found")
    return SuccessResponse(message="Profile deleted")


# ── Policies ─────────────────────────────────────────────────────

@app.get("/api/v1/policies")
async def list_policies(resource_type: Optional[str] = None):
    """List all policy rules."""
    rules = policy_engine.list_rules(resource_type=resource_type)
    return [r.to_dict() for r in rules]


@app.post("/api/v1/policies")
async def create_policy(body: dict):
    """Create a new policy rule."""
    rule = PolicyRule(
        name=body.get("name", ""),
        resource_type=body.get("resource_type", "cpu"),
        limit_value=body.get("limit_value", 0.0),
        policy_type=PolicyType(body.get("policy_type", "soft")),
        action=PolicyAction(body.get("action", "warn")),
        node_id=body.get("node_id"),
        profile_id=body.get("profile_id"),
        enabled=body.get("enabled", True),
    )
    policy_engine.add_rule(rule)
    return rule.to_dict()


@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a policy rule by ID."""
    rule = policy_engine.get_rule(policy_id)
    if not rule:
        raise HTTPException(404, "Policy not found")
    return rule.to_dict()


@app.delete("/api/v1/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Delete a policy rule."""
    result = policy_engine.remove_rule(policy_id)
    if not result:
        raise HTTPException(404, "Policy not found")
    return SuccessResponse(message="Policy deleted")


# ── Leases ───────────────────────────────────────────────────────

@app.get("/api/v1/leases")
async def list_leases(node_id: Optional[str] = None, task_id: Optional[str] = None):
    """List resource leases."""
    if task_id:
        leases = lease_manager.get_task_leases(task_id)
    elif node_id:
        leases = lease_manager.get_node_leases(node_id)
    else:
        # Return all active leases
        leases = [
            l for l in lease_manager._leases.values()
            if l.state == LeaseState.ACTIVE
        ]
    return [l.to_dict() for l in leases]


@app.post("/api/v1/leases")
async def create_lease(body: dict):
    """Create a resource lease."""
    lease = lease_manager.create_lease(
        task_id=body["task_id"],
        node_id=body["node_id"],
        cpu_threads=body.get("cpu_threads"),
        memory_bytes=body.get("memory_bytes"),
        vram_bytes=body.get("vram_bytes"),
    )
    if not lease:
        raise HTTPException(400, "Insufficient resources for lease")
    return lease.to_dict()


@app.delete("/api/v1/leases/{lease_id}")
async def release_lease(lease_id: str):
    """Release a resource lease."""
    result = lease_manager.release_lease(lease_id)
    if not result:
        raise HTTPException(404, "Lease not found or already released")
    return SuccessResponse(message="Lease released")


@app.get("/api/v1/nodes/{node_id}/usage")
async def get_node_usage(node_id: str):
    """Get resource usage for a node."""
    usage = lease_manager.get_node_usage(node_id)
    if not usage:
        raise HTTPException(404, "Node not found")
    return usage.to_dict()


# ── Providers ────────────────────────────────────────────────────

@app.get("/api/v1/providers", response_model=List[ProviderResponse])
async def list_providers():
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(ProviderModel))
        providers = result.scalars().all()
        return [
            ProviderResponse(
                provider_id=p.id,
                provider_type=p.provider_type,
                endpoint=p.endpoint,
                name=p.name,
                is_available=p.is_available,
                models=p.models or [],
            )
            for p in providers
        ]


@app.post("/api/v1/providers", response_model=ProviderResponse)
async def create_provider(req: ProviderCreate):
    async with async_session() as session:
        provider = ProviderModel(
            id=str(uuid.uuid4()),
            provider_type=req.provider_type.value,
            endpoint=req.endpoint,
            name=req.name,
            extra_config=req.extra_config,
        )
        session.add(provider)
        await session.commit()
        return ProviderResponse(
            provider_id=provider.id,
            provider_type=provider.provider_type,
            endpoint=provider.endpoint,
            name=provider.name,
        )


# ── Storage ──────────────────────────────────────────────────────

@app.get("/api/v1/storage", response_model=List[StorageLocation])
async def list_storage():
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(StorageLocationModel))
        locations = result.scalars().all()
        return [
            StorageLocation(
                location_id=l.id,
                node_id=l.node_id,
                path=l.path,
                category=l.category,
                total_bytes=l.total_bytes,
                used_bytes=l.used_bytes,
                free_bytes=l.free_bytes,
                is_available=l.is_available,
            )
            for l in locations
        ]


# ── Events ───────────────────────────────────────────────────────

@app.get("/api/v1/events", response_model=List[Event])
async def list_events(limit: int = 100):
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(
            select(EventModel).order_by(EventModel.timestamp.desc()).limit(limit)
        )
        events = result.scalars().all()
        return [
            Event(
                event_id=e.id,
                event_type=e.event_type,
                source_node_id=e.source_node_id,
                source_task_id=e.source_task_id,
                message=e.message,
                details=e.details or {},
                timestamp=e.timestamp,
            )
            for e in events
        ]


# ── WebSocket ────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"echo": data, "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        pass


# ── Enrollment ───────────────────────────────────────────────────

@app.post("/api/v1/enrollment/create", response_model=EnrollmentToken)
async def create_enrollment_token(expires_hours: int = 24):
    async with async_session() as session:
        from datetime import timedelta
        token = EnrollmentTokenModel(
            id=str(uuid.uuid4()),
            token=uuid.uuid4().hex[:16],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        )
        session.add(token)
        await session.commit()
        return EnrollmentToken(
            token_id=token.id,
            token=token.token,
            expires_at=token.expires_at,
        )
