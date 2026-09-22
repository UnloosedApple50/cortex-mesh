"""
Tests for CortexMesh enhanced API (models, metrics, health, alerts).
"""

import pytest
from httpx import AsyncClient, ASGITransport

from cortexmesh.server.api import app
from cortexmesh.database import engine, Base


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


class TestClusterHealthEndpoint:
    async def test_cluster_health(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/cluster/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("healthy", "warning", "degraded", "critical")
            assert "total_nodes" in data
            assert "active_alerts" in data


class TestClusterMetricsEndpoint:
    async def test_cluster_metrics_summary_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/cluster/metrics/summary")
            assert resp.status_code == 200

    async def test_cluster_metrics_with_type(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/cluster/metrics/summary",
                params={"metric_type": "cpu_usage_percent"},
            )
            assert resp.status_code == 200


class TestClusterAlertsEndpoint:
    async def test_cluster_alerts_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/cluster/alerts")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_cluster_alerts_with_severity(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/cluster/alerts",
                params={"severity": "critical"},
            )
            assert resp.status_code == 200


class TestModelManagementAPI:
    async def test_list_models_empty(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/models")
            assert resp.status_code == 200
            assert resp.json() == []

    async def test_register_model(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/models",
                json={
                    "name": "llama3",
                    "provider_type": "ollama",
                    "size_bytes": 4000000000,
                    "requires_gpu": True,
                    "vram_gb": 8.0,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "llama3"
            assert data["requires_gpu"] is True

    async def test_list_models_after_register(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/v1/models",
                json={"name": "llama3", "provider_type": "ollama"},
            )
            resp = await client.get("/api/v1/models")
            models = resp.json()
            assert len(models) == 1

    async def test_get_model_by_id(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg = await client.post(
                "/api/v1/models",
                json={"name": "test-model"},
            )
            model_id = reg.json()["model_id"]
            
            resp = await client.get(f"/api/v1/models/{model_id}")
            assert resp.status_code == 200
            assert resp.json()["name"] == "test-model"

    async def test_get_model_not_found(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/models/nonexistent-id")
            assert resp.status_code == 404

    async def test_stage_model(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg = await client.post(
                "/api/v1/models",
                json={"name": "stage-test"},
            )
            model_id = reg.json()["model_id"]
            
            resp = await client.post(
                f"/api/v1/models/{model_id}/stage",
                json={"node_ids": ["node-1", "node-2"]},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["state"] == "staging"

    async def test_sync_model(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg = await client.post(
                "/api/v1/models",
                json={"name": "sync-test"},
            )
            model_id = reg.json()["model_id"]
            
            resp = await client.post(
                f"/api/v1/models/{model_id}/sync",
                json={"source_node_id": "node-1", "target_node_ids": ["node-2"]},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["state"] == "syncing"

    async def test_mark_model_available(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg = await client.post(
                "/api/v1/models",
                json={"name": "avail-test"},
            )
            model_id = reg.json()["model_id"]
            
            resp = await client.post(
                f"/api/v1/models/{model_id}/available",
                json={"node_id": "node-1"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "node-1" in data["available_node_ids"]

    async def test_delete_model(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg = await client.post(
                "/api/v1/models",
                json={"name": "delete-me"},
            )
            model_id = reg.json()["model_id"]
            
            resp = await client.delete(f"/api/v1/models/{model_id}")
            assert resp.status_code == 200
            
            resp = await client.get(f"/api/v1/models/{model_id}")
            assert resp.status_code == 404

    async def test_model_stats(self):
        from cortexmesh.server import api
        api.model_manager._models.clear()
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/v1/models",
                json={"name": "stat-model1", "requires_gpu": True},
            )
            await client.post(
                "/api/v1/models",
                json={"name": "stat-model2", "requires_gpu": False},
            )
            resp = await client.get("/api/v1/models/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_models"] == 2
            assert data["gpu_models"] == 1

    async def test_node_models(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/v1/models",
                json={"name": "node-model"},
            )
            # Get models for nonexistent node returns empty
            resp = await client.get("/api/v1/nodes/fake-node/models")
            assert resp.status_code == 200


class TestAlertManagementAPI:
    async def test_acknowledge_and_resolve_alert(self):
        """Test acknowledging and resolving an alert."""
        from cortexmesh.server.api import health_monitor
        
        # Create a test alert
        health_monitor.record_node_offline("test-node")
        alerts = health_monitor.get_active_alerts()
        if alerts:
            alert_id = alerts[0].alert_id
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Acknowledge
                resp = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "acknowledged"
                
                # Resolve
                resp = await client.post(f"/api/v1/alerts/{alert_id}/resolve")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "resolved"
        
    async def test_acknowledge_nonexistent_alert(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/alerts/fake-id/acknowledge")
            assert resp.status_code == 404

    async def test_resolve_nonexistent_alert(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/alerts/fake-id/resolve")
            assert resp.status_code == 404


class TestNodeHealthAndMetricsAPI:
    async def test_node_health(self):
        """Test getting node health status."""
        from cortexmesh.server.api import health_monitor
        health_monitor.record_node_heartbeat("test-node")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/nodes/test-node/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["node_id"] == "test-node"
            assert data["state"] == "online"

    async def test_node_health_not_found(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/nodes/unknown-node/health")
            assert resp.status_code == 404

    async def test_node_metrics(self):
        """Test getting node metrics."""
        from cortexmesh.server.api import metrics_collector
        metrics_collector.record_sample("test-node", __import__("cortexmesh.monitor.metrics", fromlist=["MetricType"]).MetricType.CPU_USAGE, 75.0)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/nodes/test-node/metrics")
            assert resp.status_code == 200
            data = resp.json()
            assert "cpu_usage_percent" in data
