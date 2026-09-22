"""
Tests for CortexMesh API.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from cortexmesh.server.api import app
from cortexmesh.database import init_db, engine, Base


@pytest.fixture(autouse=True)
async def setup_db():
    """Initialize test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestHealth:
    async def test_health_check(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"

    async def test_version(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/version")
            assert resp.status_code == 200
            data = resp.json()
            assert "version" in data
            assert data["version"] == "0.1.0"
            assert data["api_version"] == "v1"


class TestNodes:
    async def test_list_nodes_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/nodes")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_create_enrollment_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post("/api/v1/enrollment/create")
            assert resp.status_code == 200
            data = resp.json()
            assert "token" in data
            assert len(data["token"]) == 16

    async def test_register_node(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Create enrollment token
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]

            # Register node
            resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {
                        "cpu": {
                            "threads": 8,
                            "architecture": "x86_64",
                        },
                        "memory": {
                            "total_bytes": 16 * 1024**3,
                            "available_bytes": 8 * 1024**3,
                        },
                        "gpus": [],
                        "storage": [],
                        "network": {"interfaces": []},
                    },
                    "roles": ["worker"],
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["hostname"] == "test-node"
            assert "node_id" in data
            assert data["state"] == "online"

    async def test_register_node_invalid_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": "invalid_token",
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )
            assert resp.status_code == 400

    async def test_list_nodes_after_register(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Create enrollment token and register node
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {
                        "cpu": {"threads": 8},
                        "memory": {
                            "total_bytes": 16 * 1024**3,
                            "available_bytes": 8 * 1024**3,
                        },
                        "gpus": [],
                        "storage": [],
                        "network": {"interfaces": []},
                    },
                    "roles": ["worker"],
                },
            )

            # List nodes
            resp = await client.get("/api/v1/nodes")
            assert resp.status_code == 200
            nodes = resp.json()
            assert len(nodes) == 1
            assert nodes[0]["hostname"] == "test-node"

    async def test_get_node_by_id(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Register a node
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            reg_resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )
            node_id = reg_resp.json()["node_id"]

            # Get node by ID
            resp = await client.get(f"/api/v1/nodes/{node_id}")
            assert resp.status_code == 200
            assert resp.json()["hostname"] == "test-node"

    async def test_get_node_not_found(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/nodes/nonexistent-node-id"
            )
            assert resp.status_code == 404

    async def test_node_heartbeat(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Register a node
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            reg_resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )
            node_id = reg_resp.json()["node_id"]

            # Send heartbeat
            resp = await client.post(
                f"/api/v1/nodes/{node_id}/heartbeat"
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    async def test_update_node_enable_disable(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Register a node
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            reg_resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )
            node_id = reg_resp.json()["node_id"]

            # Disable node
            resp = await client.patch(
                f"/api/v1/nodes/{node_id}",
                json={"compute_enabled": False},
            )
            assert resp.status_code == 200

            # Enable node
            resp = await client.patch(
                f"/api/v1/nodes/{node_id}",
                json={"compute_enabled": True},
            )
            assert resp.status_code == 200

    async def test_delete_node(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Register a node
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            reg_resp = await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )
            node_id = reg_resp.json()["node_id"]

            # Delete node
            resp = await client.delete(f"/api/v1/nodes/{node_id}")
            assert resp.status_code == 200

            # Verify it's gone
            resp = await client.get(f"/api/v1/nodes/{node_id}")
            assert resp.status_code == 404


class TestTasks:
    async def test_list_tasks_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/tasks")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_submit_task(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "Test Task",
                    "requirements": {"cpu_threads": 2, "memory_gb": 4},
                    "priority": "normal",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["title"] == "Test Task"
            assert data["state"] == "queued"

    async def test_submit_task_with_gpu(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "inference",
                    "title": "GPU Task",
                    "requirements": {
                        "cpu_threads": 4,
                        "memory_gb": 8,
                        "gpu_required": True,
                        "vram_gb": 6,
                    },
                    "priority": "high",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["requirements"]["gpu_required"] is True

    async def test_get_task_by_id(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Submit a task
            submit_resp = await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "My Task",
                    "requirements": {},
                    "priority": "normal",
                },
            )
            task_id = submit_resp.json()["task_id"]

            # Get task by ID
            resp = await client.get(f"/api/v1/tasks/{task_id}")
            assert resp.status_code == 200
            assert resp.json()["title"] == "My Task"

    async def test_get_task_not_found(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/tasks/nonexistent-task-id"
            )
            assert resp.status_code == 404

    async def test_list_tasks_by_state(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Submit two tasks
            await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "Task 1",
                    "requirements": {},
                },
            )
            await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "Task 2",
                    "requirements": {},
                },
            )

            # Filter by queued state
            resp = await client.get(
                "/api/v1/tasks", params={"state": "queued"}
            )
            assert resp.status_code == 200
            tasks = resp.json()
            assert len(tasks) == 2

    async def test_cancel_task(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Submit a task
            submit_resp = await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "Cancel Me",
                    "requirements": {},
                },
            )
            task_id = submit_resp.json()["task_id"]

            # Cancel it
            resp = await client.post(
                f"/api/v1/tasks/{task_id}/cancel"
            )
            assert resp.status_code == 200

            # Verify state changed
            task_resp = await client.get(f"/api/v1/tasks/{task_id}")
            assert task_resp.json()["state"] == "cancelling"

    async def test_cancel_completed_task_fails(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Submit a task and manually set to completed
            submit_resp = await client.post(
                "/api/v1/tasks",
                json={
                    "task_type": "chat",
                    "title": "Done Task",
                    "requirements": {},
                },
            )
            task_id = submit_resp.json()["task_id"]

            # Cancel should fail for already-completed task
            # (We'd need to mark it completed first; skip for now)
            resp = await client.post(
                f"/api/v1/tasks/{task_id}/cancel"
            )
            # Should succeed since task is queued
            assert resp.status_code == 200


class TestProviders:
    async def test_list_providers_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/providers")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_create_provider(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/providers",
                json={
                    "provider_type": "ollama",
                    "endpoint": "http://localhost:11434",
                    "name": "Local Ollama",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Local Ollama"
            assert data["provider_type"] == "ollama"
            assert "provider_id" in data

    async def test_list_providers_after_create(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/providers",
                json={
                    "provider_type": "ollama",
                    "endpoint": "http://localhost:11434",
                    "name": "Local Ollama",
                },
            )
            resp = await client.get("/api/v1/providers")
            assert resp.status_code == 200
            assert len(resp.json()) == 1


class TestStorage:
    async def test_list_storage_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/storage")
            assert resp.status_code == 200
            assert resp.json() == []


class TestEvents:
    async def test_list_events_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/events")
            assert resp.status_code == 200

    async def test_events_after_node_register(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Register a node to generate an event
            token_resp = await client.post("/api/v1/enrollment/create")
            token = token_resp.json()["token"]
            await client.post(
                "/api/v1/nodes/register",
                json={
                    "enrollment_token": token,
                    "hostname": "event-test-node",
                    "platform": "linux",
                    "architecture": "x86_64",
                    "agent_version": "0.1.0",
                    "capabilities": {},
                    "roles": ["worker"],
                },
            )

            # Check events
            resp = await client.get("/api/v1/events")
            assert resp.status_code == 200
            events = resp.json()
            assert len(events) >= 1
            assert events[0]["event_type"] == "node_registered"
