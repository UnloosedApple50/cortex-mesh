"""
Tests for CortexMesh policies system.
"""

import pytest

from cortexmesh.core.policies import (
    PolicyAction, PolicyCheckResult, PolicyEngine, PolicyRule, PolicyType
)


class TestPolicyRule:
    def test_create_rule(self):
        rule = PolicyRule(
            name="CPU Limit",
            resource_type="cpu",
            limit_value=90.0,
            policy_type=PolicyType.HARD,
            action=PolicyAction.REJECT,
        )
        assert rule.name == "CPU Limit"
        assert rule.resource_type == "cpu"
        assert rule.limit_value == 90.0
        assert rule.policy_type == PolicyType.HARD
        assert rule.action == PolicyAction.REJECT
        assert rule.enabled is True

    def test_to_dict(self):
        rule = PolicyRule(name="test", resource_type="memory", limit_value=80.0)
        d = rule.to_dict()
        assert d["name"] == "test"
        assert d["resource_type"] == "memory"
        assert d["limit_value"] == 80.0
        assert d["policy_type"] == "soft"


class TestPolicyEngine:
    def test_add_and_get_rule(self):
        engine = PolicyEngine()
        rule = PolicyRule(name="test", resource_type="cpu", limit_value=90.0)
        engine.add_rule(rule)
        retrieved = engine.get_rule(rule.policy_id)
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_remove_rule(self):
        engine = PolicyEngine()
        rule = PolicyRule(name="test", resource_type="cpu", limit_value=90.0)
        engine.add_rule(rule)
        result = engine.remove_rule(rule.policy_id)
        assert result is True
        assert engine.get_rule(rule.policy_id) is None

    def test_list_rules(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(name="cpu", resource_type="cpu", limit_value=90.0))
        engine.add_rule(PolicyRule(name="memory", resource_type="memory", limit_value=80.0))
        rules = engine.list_rules()
        assert len(rules) == 2

    def test_list_rules_filtered(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(name="cpu", resource_type="cpu", limit_value=90.0))
        engine.add_rule(PolicyRule(name="memory", resource_type="memory", limit_value=80.0))
        cpu_rules = engine.list_rules(resource_type="cpu")
        assert len(cpu_rules) == 1
        assert cpu_rules[0].resource_type == "cpu"

    def test_check_resource_within_limit(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            name="CPU Soft",
            resource_type="cpu",
            limit_value=90.0,
            policy_type=PolicyType.SOFT,
        ))
        result = engine.check_resource("cpu", current_usage=50.0, requested=20.0)
        assert result.allowed is True

    def test_check_resource_exceeds_hard_limit(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            name="CPU Hard",
            resource_type="cpu",
            limit_value=90.0,
            policy_type=PolicyType.HARD,
            action=PolicyAction.REJECT,
        ))
        result = engine.check_resource("cpu", current_usage=80.0, requested=20.0)
        assert result.allowed is False
        assert result.action == PolicyAction.REJECT

    def test_check_resource_exceeds_soft_limit(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            name="CPU Soft",
            resource_type="cpu",
            limit_value=80.0,
            policy_type=PolicyType.SOFT,
            action=PolicyAction.WARN,
        ))
        result = engine.check_resource("cpu", current_usage=70.0, requested=20.0)
        assert result.allowed is True  # Soft limits allow but warn
        assert result.action == PolicyAction.WARN

    def test_check_resource_monitoring_only(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            name="CPU Monitor",
            resource_type="cpu",
            limit_value=80.0,
            policy_type=PolicyType.MONITORING_ONLY,
            action=PolicyAction.LOG,
        ))
        result = engine.check_resource("cpu", current_usage=90.0, requested=10.0)
        assert result.allowed is True
        assert result.action == PolicyAction.LOG

    def test_check_task_eligibility(self):
        engine = PolicyEngine()
        result = engine.check_task_eligibility(
            cpu_threads=4,
            memory_gb=8,
            node_cpu_available=8,
            node_memory_available_gb=16,
        )
        assert result.allowed is True

    def test_check_task_eligibility_insufficient_cpu(self):
        engine = PolicyEngine()
        result = engine.check_task_eligibility(
            cpu_threads=8,
            node_cpu_available=4,
        )
        assert result.allowed is False
        assert "Insufficient CPU" in result.reason

    def test_check_task_eligibility_insufficient_memory(self):
        engine = PolicyEngine()
        result = engine.check_task_eligibility(
            memory_gb=16,
            node_memory_available_gb=8,
        )
        assert result.allowed is False
        assert "Insufficient memory" in result.reason

    def test_check_task_eligibility_insufficient_vram(self):
        engine = PolicyEngine()
        result = engine.check_task_eligibility(
            vram_gb=8,
            node_vram_available_gb=4,
        )
        assert result.allowed is False
        assert "Insufficient VRAM" in result.reason

    def test_get_default_policies(self):
        engine = PolicyEngine()
        defaults = engine.get_default_policies()
        assert len(defaults) >= 3
        # Should have CPU, memory, and VRAM rules
        resource_types = {r.resource_type for r in defaults}
        assert "cpu" in resource_types
        assert "memory" in resource_types
        assert "vram" in resource_types

    def test_disabled_rules_ignored(self):
        engine = PolicyEngine()
        rule = PolicyRule(
            name="Disabled",
            resource_type="cpu",
            limit_value=50.0,
            policy_type=PolicyType.HARD,
            enabled=False,
        )
        engine.add_rule(rule)
        result = engine.check_resource("cpu", current_usage=80.0, requested=10.0)
        assert result.allowed is True  # Disabled rule should not block

    def test_node_specific_rule(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule(
            name="Node CPU",
            resource_type="cpu",
            limit_value=70.0,
            policy_type=PolicyType.HARD,
            node_id="node-1",
        ))
        # Should apply to node-1
        result = engine.check_resource("cpu", current_usage=60.0, requested=20.0, node_id="node-1")
        assert result.allowed is False
        # Should not apply to node-2
        result = engine.check_resource("cpu", current_usage=60.0, requested=20.0, node_id="node-2")
        assert result.allowed is True
