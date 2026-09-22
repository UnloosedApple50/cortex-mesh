"""
CortexMesh — Policies system.

Policies define resource management strategies:
- HARD: Strict enforcement, tasks rejected if limit exceeded
- SOFT: Best effort, warnings issued if limit exceeded
- MONITORING_ONLY: Track but don't enforce limits
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PolicyType(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    MONITORING_ONLY = "monitoring_only"


class PolicyAction(str, Enum):
    REJECT = "reject"
    WARN = "warn"
    LOG = "log"
    THROTTLE = "throttle"


@dataclass
class PolicyRule:
    """
    A single policy rule for resource management.

    Attributes:
        policy_id: Unique identifier
        name: Human-readable name
        resource_type: Type of resource (cpu, memory, vram, etc.)
        limit_value: The limit value (interpretation depends on resource_type)
        policy_type: How strictly to enforce
        enabled: Whether this rule is active
        action: Action to take when limit is exceeded
        node_id: Optional node ID to scope this rule to
        profile_id: Optional profile ID to scope this rule to
    """
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    resource_type: str = "cpu"
    limit_value: float = 0.0
    policy_type: PolicyType = PolicyType.SOFT
    enabled: bool = True
    action: PolicyAction = PolicyAction.WARN
    node_id: Optional[str] = None
    profile_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "resource_type": self.resource_type,
            "limit_value": self.limit_value,
            "policy_type": self.policy_type.value,
            "enabled": self.enabled,
            "action": self.action.value,
            "node_id": self.node_id,
            "profile_id": self.profile_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PolicyCheckResult:
    """Result of a policy check."""
    allowed: bool
    policy_id: Optional[str] = None
    rule_name: Optional[str] = None
    reason: Optional[str] = None
    action: Optional[PolicyAction] = None
    usage_percent: float = 0.0
    limit_value: float = 0.0


class PolicyEngine:
    """
    Evaluates policies against resource usage and task requirements.
    """

    def __init__(self):
        self._rules: Dict[str, PolicyRule] = {}
        self._violation_callbacks: List[Callable] = []

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a policy rule."""
        self._rules[rule.policy_id] = rule

    def remove_rule(self, policy_id: str) -> bool:
        """Remove a policy rule."""
        if policy_id in self._rules:
            del self._rules[policy_id]
            return True
        return False

    def get_rule(self, policy_id: str) -> Optional[PolicyRule]:
        """Get a rule by ID."""
        return self._rules.get(policy_id)

    def list_rules(self, resource_type: Optional[str] = None,
                   node_id: Optional[str] = None) -> List[PolicyRule]:
        """List all rules, optionally filtered."""
        rules = list(self._rules.values())
        if resource_type:
            rules = [r for r in rules if r.resource_type == resource_type]
        if node_id:
            rules = [r for r in rules if r.node_id is None or r.node_id == node_id]
        return [r for r in rules if r.enabled]

    def check_resource(self, resource_type: str, current_usage: float,
                       requested: float, node_id: Optional[str] = None,
                       profile_id: Optional[str] = None) -> PolicyCheckResult:
        """
        Check if a resource request complies with policies.

        Args:
            resource_type: Type of resource (cpu, memory, vram)
            current_usage: Current usage value
            requested: Additional amount requested
            node_id: Optional node to scope rules to
            profile_id: Optional profile to scope rules to

        Returns:
            PolicyCheckResult with the decision
        """
        rules = self.list_rules(resource_type=resource_type, node_id=node_id)

        total = current_usage + requested

        for rule in rules:
            if not rule.enabled:
                continue
            # Also check profile-specific rules
            if rule.profile_id and rule.profile_id != profile_id:
                continue

            if total > rule.limit_value:
                if rule.policy_type == PolicyType.HARD:
                    return PolicyCheckResult(
                        allowed=False,
                        policy_id=rule.policy_id,
                        rule_name=rule.name,
                        reason=f"HARD limit exceeded: {total:.1f} > {rule.limit_value:.1f}",
                        action=rule.action,
                        usage_percent=total,
                        limit_value=rule.limit_value,
                    )
                elif rule.policy_type == PolicyType.SOFT:
                    # Soft limit: allow but warn
                    return PolicyCheckResult(
                        allowed=True,
                        policy_id=rule.policy_id,
                        rule_name=rule.name,
                        reason=f"SOFT limit warning: {total:.1f} > {rule.limit_value:.1f}",
                        action=PolicyAction.WARN,
                        usage_percent=total,
                        limit_value=rule.limit_value,
                    )
                else:
                    # MONITORING_ONLY
                    return PolicyCheckResult(
                        allowed=True,
                        policy_id=rule.policy_id,
                        rule_name=rule.name,
                        reason=f"MONITORING: {total:.1f} > {rule.limit_value:.1f}",
                        action=PolicyAction.LOG,
                        usage_percent=total,
                        limit_value=rule.limit_value,
                    )

        return PolicyCheckResult(allowed=True)

    def check_task_eligibility(self, cpu_threads: Optional[int] = None,
                               memory_gb: Optional[float] = None,
                               vram_gb: Optional[float] = None,
                               node_cpu_available: int = 0,
                               node_memory_available_gb: float = 0,
                               node_vram_available_gb: float = 0,
                               node_id: Optional[str] = None) -> PolicyCheckResult:
        """
        Check if a task is eligible to run on a node given current policies.
        """
        # Check CPU
        if cpu_threads and node_cpu_available < cpu_threads:
            return PolicyCheckResult(
                allowed=False,
                reason=f"Insufficient CPU: {node_cpu_available} < {cpu_threads}",
            )

        # Check memory
        if memory_gb and node_memory_available_gb < memory_gb:
            return PolicyCheckResult(
                allowed=False,
                reason=f"Insufficient memory: {node_memory_available_gb:.1f}GB < {memory_gb}GB",
            )

        # Check VRAM
        if vram_gb and node_vram_available_gb < vram_gb:
            return PolicyCheckResult(
                allowed=False,
                reason=f"Insufficient VRAM: {node_vram_available_gb:.1f}GB < {vram_gb}GB",
            )

        return PolicyCheckResult(allowed=True)

    def on_violation(self, callback: Callable) -> None:
        """Register a callback for policy violations."""
        self._violation_callbacks.append(callback)

    def get_default_policies(self) -> List[PolicyRule]:
        """Get sensible default policies."""
        return [
            PolicyRule(
                name="CPU Hard Limit",
                resource_type="cpu",
                limit_value=95.0,
                policy_type=PolicyType.HARD,
                action=PolicyAction.REJECT,
            ),
            PolicyRule(
                name="Memory Hard Limit",
                resource_type="memory",
                limit_value=95.0,
                policy_type=PolicyType.HARD,
                action=PolicyAction.REJECT,
            ),
            PolicyRule(
                name="VRAM Hard Limit",
                resource_type="vram",
                limit_value=98.0,
                policy_type=PolicyType.HARD,
                action=PolicyAction.REJECT,
            ),
            PolicyRule(
                name="CPU Soft Limit",
                resource_type="cpu",
                limit_value=80.0,
                policy_type=PolicyType.SOFT,
                action=PolicyAction.WARN,
            ),
            PolicyRule(
                name="Memory Soft Limit",
                resource_type="memory",
                limit_value=80.0,
                policy_type=PolicyType.SOFT,
                action=PolicyAction.WARN,
            ),
        ]
