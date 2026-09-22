"""
Tests for CortexMesh resource lease system.
"""

import pytest
from datetime import datetime, timezone, timedelta

from cortexmesh.core.leases import (
    LeaseManager, LeaseState, ResourceLease, NodeResourceUsage
)


class TestResourceLease:
    def test_create_lease(self):
        lease = ResourceLease(
            lease_id="lease-1",
            task_id="task-1",
            node_id="node-1",
            cpu_threads=4,
            memory_bytes=8 * 1024**3,
        )
        assert lease.lease_id == "lease-1"
        assert lease.state == LeaseState.ACTIVE
        assert lease.cpu_threads == 4
        assert lease.memory_bytes == 8 * 1024**3

    def test_to_dict(self):
        lease = ResourceLease(
            lease_id="lease-1",
            task_id="task-1",
            node_id="node-1",
        )
        d = lease.to_dict()
        assert d["lease_id"] == "lease-1"
        assert d["state"] == "active"


class TestNodeResourceUsage:
    def test_create_usage(self):
        usage = NodeResourceUsage(
            node_id="node-1",
            cpu_threads_total=16,
            memory_bytes_total=64 * 1024**3,
        )
        assert usage.cpu_threads_total == 16
        assert usage.cpu_available == 16
        assert usage.memory_available == 64 * 1024**3

    def test_cpu_available(self):
        usage = NodeResourceUsage(
            node_id="node-1",
            cpu_threads_total=16,
            cpu_threads_used=4,
        )
        assert usage.cpu_available == 12

    def test_memory_available(self):
        usage = NodeResourceUsage(
            node_id="node-1",
            memory_bytes_total=64 * 1024**3,
            memory_bytes_used=16 * 1024**3,
        )
        assert usage.memory_available == 48 * 1024**3

    def test_can_reserve(self):
        usage = NodeResourceUsage(
            node_id="node-1",
            cpu_threads_total=16,
            cpu_threads_used=4,
            memory_bytes_total=64 * 1024**3,
            memory_bytes_used=16 * 1024**3,
        )
        assert usage.can_reserve(cpu=8) is True
        assert usage.can_reserve(cpu=20) is False
        assert usage.can_reserve(memory=32 * 1024**3) is True
        assert usage.can_reserve(memory=64 * 1024**3) is False

    def test_to_dict(self):
        usage = NodeResourceUsage(
            node_id="node-1",
            cpu_threads_total=16,
            cpu_threads_used=4,
        )
        d = usage.to_dict()
        assert d["node_id"] == "node-1"
        assert d["cpu"]["total"] == 16
        assert d["cpu"]["used"] == 4
        assert d["cpu"]["available"] == 12


class TestLeaseManager:
    def test_register_node(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16, memory_bytes=64 * 1024**3)
        usage = manager.get_node_usage("node-1")
        assert usage is not None
        assert usage.cpu_threads_total == 16

    def test_create_lease(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16, memory_bytes=64 * 1024**3)
        lease = manager.create_lease(
            task_id="task-1",
            node_id="node-1",
            cpu_threads=4,
            memory_bytes=8 * 1024**3,
        )
        assert lease is not None
        assert lease.state == LeaseState.ACTIVE
        assert lease.cpu_threads == 4

    def test_create_lease_insufficient_resources(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=4, memory_bytes=8 * 1024**3)
        lease = manager.create_lease(
            task_id="task-1",
            node_id="node-1",
            cpu_threads=8,
        )
        assert lease is None

    def test_create_lease_unknown_node(self):
        manager = LeaseManager()
        lease = manager.create_lease(
            task_id="task-1",
            node_id="unknown-node",
            cpu_threads=4,
        )
        assert lease is None

    def test_release_lease(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16)
        lease = manager.create_lease(
            task_id="task-1",
            node_id="node-1",
            cpu_threads=4,
        )
        assert lease is not None
        
        result = manager.release_lease(lease.lease_id)
        assert result is True
        assert lease.state == LeaseState.RELEASED
        
        # Resources should be freed
        usage = manager.get_node_usage("node-1")
        assert usage.cpu_threads_used == 0

    def test_release_nonexistent_lease(self):
        manager = LeaseManager()
        result = manager.release_lease("nonexistent")
        assert result is False

    def test_release_task_leases(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16)
        
        lease1 = manager.create_lease("task-1", "node-1", cpu_threads=2)
        lease2 = manager.create_lease("task-1", "node-1", cpu_threads=4)
        lease3 = manager.create_lease("task-2", "node-1", cpu_threads=2)
        
        count = manager.release_task_leases("task-1")
        assert count == 2
        assert lease1.state == LeaseState.RELEASED
        assert lease2.state == LeaseState.RELEASED
        assert lease3.state == LeaseState.ACTIVE

    def test_get_node_leases(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16)
        
        lease1 = manager.create_lease("task-1", "node-1", cpu_threads=2)
        lease2 = manager.create_lease("task-2", "node-1", cpu_threads=4)
        
        leases = manager.get_node_leases("node-1")
        assert len(leases) == 2

    def test_get_all_usage(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16)
        manager.register_node("node-2", cpu_threads=8)
        
        all_usage = manager.get_all_usage()
        assert len(all_usage) == 2
        assert "node-1" in all_usage
        assert "node-2" in all_usage

    def test_cleanup_expired(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16)
        
        # Create lease with old timestamp
        lease = manager.create_lease("task-1", "node-1", cpu_threads=2)
        lease.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        
        cleaned = manager.cleanup_expired(max_age_seconds=3600)
        assert cleaned == 1

    def test_resource_reservation_updates(self):
        manager = LeaseManager()
        manager.register_node("node-1", cpu_threads=16, memory_bytes=64 * 1024**3)
        
        manager.create_lease("task-1", "node-1", cpu_threads=4, memory_bytes=8 * 1024**3)
        
        usage = manager.get_node_usage("node-1")
        assert usage.cpu_threads_used == 4
        assert usage.memory_bytes_used == 8 * 1024**3
        assert usage.cpu_available == 12
        assert usage.memory_available == 56 * 1024**3
