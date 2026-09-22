"""
CortexMesh — Profiles and policies system.

Profiles define resource limits and scheduling preferences for nodes.
Policies define how resources are managed (hard limits, soft limits, monitoring only).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ResourceProfile:
    """
    A resource profile defines limits and preferences for node participation.

    Attributes:
        profile_id: Unique identifier
        name: Human-readable name
        description: Optional description
        cpu_limit_percent: Maximum CPU usage percentage (0-100)
        memory_limit_percent: Maximum memory usage percentage (0-100)
        gpu_scheduling_limit_percent: Maximum GPU scheduling percentage (0-100)
        priority: Task priority for this profile
        allowed_hours_start: Start hour (0-23) for allowed scheduling window
        allowed_hours_end: End hour (0-23) for allowed scheduling window
        allowed_node_roles: Only schedule on nodes with these roles
        max_concurrent_tasks: Maximum number of concurrent tasks
        preemptible: Whether tasks under this profile can be preempted
    """
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default"
    description: Optional[str] = None
    cpu_limit_percent: Optional[float] = None
    memory_limit_percent: Optional[float] = None
    gpu_scheduling_limit_percent: Optional[float] = None
    priority: str = "normal"
    allowed_hours_start: Optional[int] = None
    allowed_hours_end: Optional[int] = None
    allowed_node_roles: List[str] = field(default_factory=list)
    max_concurrent_tasks: Optional[int] = None
    preemptible: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def is_active(self, hour: Optional[int] = None) -> bool:
        """Check if this profile is active at the given hour."""
        if self.allowed_hours_start is None or self.allowed_hours_end is None:
            return True
        if hour is None:
            hour = datetime.now(timezone.utc).hour
        if self.allowed_hours_start <= self.allowed_hours_end:
            return self.allowed_hours_start <= hour <= self.allowed_hours_end
        else:
            # Wraps midnight
            return hour >= self.allowed_hours_start or hour <= self.allowed_hours_end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "cpu_limit_percent": self.cpu_limit_percent,
            "memory_limit_percent": self.memory_limit_percent,
            "gpu_scheduling_limit_percent": self.gpu_scheduling_limit_percent,
            "priority": self.priority,
            "allowed_hours_start": self.allowed_hours_start,
            "allowed_hours_end": self.allowed_hours_end,
            "allowed_node_roles": self.allowed_node_roles,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "preemptible": self.preemptible,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceProfile":
        profile = cls(
            profile_id=data.get("profile_id", str(uuid.uuid4())),
            name=data.get("name", "default"),
            description=data.get("description"),
            cpu_limit_percent=data.get("cpu_limit_percent"),
            memory_limit_percent=data.get("memory_limit_percent"),
            gpu_scheduling_limit_percent=data.get("gpu_scheduling_limit_percent"),
            priority=data.get("priority", "normal"),
            allowed_hours_start=data.get("allowed_hours_start"),
            allowed_hours_end=data.get("allowed_hours_end"),
            allowed_node_roles=data.get("allowed_node_roles", []),
            max_concurrent_tasks=data.get("max_concurrent_tasks"),
            preemptible=data.get("preemptible", False),
        )
        if "created_at" in data and data["created_at"]:
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and data["updated_at"]:
            profile.updated_at = datetime.fromisoformat(data["updated_at"])
        return profile


class ProfileManager:
    """Manages resource profiles for the mesh."""

    def __init__(self):
        self._profiles: Dict[str, ResourceProfile] = {}

    def create_profile(self, **kwargs) -> ResourceProfile:
        """Create a new profile."""
        profile = ResourceProfile(**kwargs)
        self._profiles[profile.profile_id] = profile
        return profile

    def get_profile(self, profile_id: str) -> Optional[ResourceProfile]:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)

    def update_profile(self, profile_id: str, **kwargs) -> Optional[ResourceProfile]:
        """Update an existing profile."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = datetime.now(timezone.utc)
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False

    def list_profiles(self) -> List[ResourceProfile]:
        """List all profiles."""
        return list(self._profiles.values())

    def get_active_profiles(self, hour: Optional[int] = None) -> List[ResourceProfile]:
        """Get all profiles active at the given hour."""
        return [p for p in self._profiles.values() if p.is_active(hour)]
