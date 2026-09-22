"""
CortexMesh — Resource Lease System.

Manages CPU, memory, and VRAM reservations for tasks.
Leases are tracked in the database and released when tasks complete.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class LeaseState(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"


@dataclass
class ResourceLease:
    """A resource lease reserving resources on a node for a task."""
    lease_id: str
    task_id: str
    node_id: str
    cpu_threads: Optional[int] = None
    memory_bytes: Optional[int] = None
    vram_bytes: Optional[int] = None
    state: LeaseState = LeaseState.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    released_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "lease_id": self.lease_id,
            "task_id": self.task_id,
            "node_id": self.node_id,
            "cpu_threads": self.cpu_threads,
            "memory_bytes": self.memory_bytes,
            "vram_bytes": self.vram_bytes,
            "state": self.state.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
        }


@dataclass
class NodeResourceUsage:
    """Current resource usage and reservations on a node."""
    node_id: str
    cpu_threads_total: int = 0
    cpu_threads_used: int = 0
    memory_bytes_total: int = 0
    memory_bytes_used: int = 0
    vram_bytes_total: int = 0
    vram_bytes_used: int = 0

    @property
    def cpu_available(self) -> int:
        return max(0, self.cpu_threads_total - self.cpu_threads_used)

    @property
    def memory_available(self) -> int:
        return max(0, self.memory_bytes_total - self.memory_bytes_used)

    @property
    def vram_available(self) -> int:
        return max(0, self.vram_bytes_total - self.vram_bytes_used)

    def can_reserve(self, cpu: Optional[int] = None, memory: Optional[int] = None,
                    vram: Optional[int] = None) -> bool:
        """Check if requested resources can be reserved."""
        if cpu is not None and self.cpu_available < cpu:
            return False
        if memory is not None and self.memory_available < memory:
            return False
        if vram is not None and self.vram_available < vram:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "cpu": {
                "total": self.cpu_threads_total,
                "used": self.cpu_threads_used,
                "available": self.cpu_available,
            },
            "memory": {
                "total": self.memory_bytes_total,
                "used": self.memory_bytes_used,
                "available": self.memory_available,
            },
            "vram": {
                "total": self.vram_bytes_total,
                "used": self.vram_bytes_used,
                "available": self.vram_available,
            },
        }


class LeaseManager:
    """
    Manages resource leases for the mesh.

    Tracks reservations per node and enforces limits.
    In production, this would use the database; for now it's in-memory
    with hooks for DB persistence.
    """

    def __init__(self):
        self._leases: Dict[str, ResourceLease] = {}
        self._node_usage: Dict[str, NodeResourceUsage] = {}

    def register_node(self, node_id: str, cpu_threads: int = 0,
                      memory_bytes: int = 0, vram_bytes: int = 0) -> None:
        """Register a node's total resources."""
        self._node_usage[node_id] = NodeResourceUsage(
            node_id=node_id,
            cpu_threads_total=cpu_threads,
            memory_bytes_total=memory_bytes,
            vram_bytes_total=vram_bytes,
        )

    def update_node_resources(self, node_id: str, cpu_threads: Optional[int] = None,
                              memory_bytes: Optional[int] = None,
                              vram_bytes: Optional[int] = None) -> None:
        """Update a node's total resources."""
        if node_id not in self._node_usage:
            self._node_usage[node_id] = NodeResourceUsage(node_id=node_id)
        usage = self._node_usage[node_id]
        if cpu_threads is not None:
            usage.cpu_threads_total = cpu_threads
        if memory_bytes is not None:
            usage.memory_bytes_total = memory_bytes
        if vram_bytes is not None:
            usage.vram_bytes_total = vram_bytes

    def create_lease(self, task_id: str, node_id: str,
                     cpu_threads: Optional[int] = None,
                     memory_bytes: Optional[int] = None,
                     vram_bytes: Optional[int] = None) -> Optional[ResourceLease]:
        """
        Create a resource lease for a task on a node.

        Returns None if resources are not available.
        """
        if node_id not in self._node_usage:
            return None

        usage = self._node_usage[node_id]
        if not usage.can_reserve(cpu_threads, memory_bytes, vram_bytes):
            return None

        lease = ResourceLease(
            lease_id=str(uuid.uuid4()),
            task_id=task_id,
            node_id=node_id,
            cpu_threads=cpu_threads,
            memory_bytes=memory_bytes,
            vram_bytes=vram_bytes,
        )

        # Reserve resources
        if cpu_threads:
            usage.cpu_threads_used += cpu_threads
        if memory_bytes:
            usage.memory_bytes_used += memory_bytes
        if vram_bytes:
            usage.vram_bytes_used += vram_bytes

        self._leases[lease.lease_id] = lease
        return lease

    def release_lease(self, lease_id: str) -> bool:
        """Release a lease and free its resources."""
        lease = self._leases.get(lease_id)
        if not lease or lease.state != LeaseState.ACTIVE:
            return False

        usage = self._node_usage.get(lease.node_id)
        if usage:
            if lease.cpu_threads:
                usage.cpu_threads_used = max(0, usage.cpu_threads_used - lease.cpu_threads)
            if lease.memory_bytes:
                usage.memory_bytes_used = max(0, usage.memory_bytes_used - lease.memory_bytes)
            if lease.vram_bytes:
                usage.vram_bytes_used = max(0, usage.vram_bytes_used - lease.vram_bytes)

        lease.state = LeaseState.RELEASED
        lease.released_at = datetime.now(timezone.utc)
        return True

    def release_task_leases(self, task_id: str) -> int:
        """Release all active leases for a task. Returns count released."""
        released = 0
        for lease in self._leases.values():
            if lease.task_id == task_id and lease.state == LeaseState.ACTIVE:
                if self.release_lease(lease.lease_id):
                    released += 1
        return released

    def get_lease(self, lease_id: str) -> Optional[ResourceLease]:
        """Get a lease by ID."""
        return self._leases.get(lease_id)

    def get_task_leases(self, task_id: str) -> List[ResourceLease]:
        """Get all leases for a task."""
        return [l for l in self._leases.values() if l.task_id == task_id]

    def get_node_leases(self, node_id: str) -> List[ResourceLease]:
        """Get all active leases on a node."""
        return [
            l for l in self._leases.values()
            if l.node_id == node_id and l.state == LeaseState.ACTIVE
        ]

    def get_node_usage(self, node_id: str) -> Optional[NodeResourceUsage]:
        """Get current resource usage for a node."""
        return self._node_usage.get(node_id)

    def get_all_usage(self) -> Dict[str, NodeResourceUsage]:
        """Get resource usage for all nodes."""
        return dict(self._node_usage)

    def cleanup_expired(self, max_age_seconds: float = 3600) -> int:
        """Remove expired leases. Returns count cleaned."""
        now = datetime.now(timezone.utc)
        cleaned = 0
        for lease in list(self._leases.values()):
            if lease.state == LeaseState.ACTIVE:
                age = (now - lease.created_at).total_seconds()
                if age > max_age_seconds:
                    self.release_lease(lease.lease_id)
                    lease.state = LeaseState.EXPIRED
                    cleaned += 1
        return cleaned
