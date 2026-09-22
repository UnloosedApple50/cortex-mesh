"""
Tests for HermesMesh scheduler.
"""

import pytest
from datetime import datetime
from hermesmesh.core.scheduler import CapabilityScorer, Scheduler
from hermesmesh.models import (
    Architecture, CPUCapability, GPUCapability, GPUVendor,
    MemoryCapability, NodeCapabilities, NodeResponse, NodeRole,
    NodeState, Platform, TaskPriority, TaskRequirements, TaskSubmit,
    TaskType,
)


@pytest.fixture
def sample_node():
    """Create a sample node for testing."""
    return NodeResponse(
        node_id="test-node-1",
        hostname="test-01",
        display_name="Test Node 1",
        platform=Platform.LINUX,
        architecture=Architecture.X86_64,
        agent_version="0.1.0",
        roles=[NodeRole.WORKER],
        state=NodeState.ONLINE,
        capabilities=NodeCapabilities(
            cpu=CPUCapability(
                threads=16,
                cores_physical=8,
                architecture=Architecture.X86_64,
            ),
            memory=MemoryCapability(
                total_bytes=64 * 1024**3,
                available_bytes=32 * 1024**3,
            ),
            gpus=[
                GPUCapability(
                    vendor=GPUVendor.NVIDIA,
                    model="RTX 4060",
                    vram_bytes=8 * 1024**3,
                    monitoring_supported=True,
                )
            ],
        ),
        created_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return TaskSubmit(
        task_type=TaskType.INFERENCE,
        title="Test Inference",
        requirements=TaskRequirements(
            cpu_threads=4,
            memory_gb=8,
            gpu_required=True,
            vram_gb=6,
        ),
        priority=TaskPriority.NORMAL,
    )


@pytest.fixture
def large_node():
    """Create a large node for testing."""
    return NodeResponse(
        node_id="large-node",
        hostname="large-01",
        display_name="Large Node",
        platform=Platform.LINUX,
        architecture=Architecture.X86_64,
        agent_version="0.1.0",
        roles=[NodeRole.WORKER],
        state=NodeState.ONLINE,
        capabilities=NodeCapabilities(
            cpu=CPUCapability(
                threads=64,
                cores_physical=32,
                architecture=Architecture.X86_64,
            ),
            memory=MemoryCapability(
                total_bytes=256 * 1024**3,
                available_bytes=128 * 1024**3,
            ),
            gpus=[
                GPUCapability(
                    vendor=GPUVendor.NVIDIA,
                    model="A100",
                    vram_bytes=80 * 1024**3,
                    monitoring_supported=True,
                ),
                GPUCapability(
                    vendor=GPUVendor.NVIDIA,
                    model="A100",
                    vram_bytes=80 * 1024**3,
                    monitoring_supported=True,
                ),
            ],
        ),
        created_at=datetime(2024, 1, 1, 0, 0, 0),
    )


class TestCapabilityScorer:
    def test_score_eligible_node(self, sample_node, sample_task):
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score > 0
        assert result.node_id == "test-node-1"
        assert len(result.explanation) > 0

    def test_reject_offline_node(self, sample_node, sample_task):
        sample_node.state = NodeState.OFFLINE
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score == -1

    def test_reject_client_only_node(self, sample_node, sample_task):
        sample_node.roles = [NodeRole.CLIENT]
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score == -1

    def test_reject_insufficient_cpu(self, sample_node, sample_task):
        sample_node.capabilities.cpu.threads = 2
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score == -1

    def test_reject_insufficient_ram(self, sample_node, sample_task):
        sample_node.capabilities.memory.available_bytes = 1 * 1024**3
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score == -1

    def test_reject_no_gpu_when_required(self, sample_node, sample_task):
        sample_node.capabilities.gpus = []
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, sample_task)
        assert result.score == -1

    def test_score_higher_for_better_hardware(self, sample_node, sample_task, large_node):
        scorer = CapabilityScorer()
        small_result = scorer.score_node(sample_node, sample_task)
        large_result = scorer.score_node(large_node, sample_task)
        assert large_result.score > small_result.score

    def test_score_no_gpu_requirement(self, sample_node):
        """Test scoring when task doesn't require GPU."""
        task = TaskSubmit(
            task_type=TaskType.CHAT,
            title="CPU Task",
            requirements=TaskRequirements(
                cpu_threads=4,
                memory_gb=8,
            ),
            priority=TaskPriority.NORMAL,
        )
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, task)
        assert result.score > 0

    def test_score_with_minimal_requirements(self, sample_node):
        """Test scoring with minimal task requirements."""
        task = TaskSubmit(
            task_type=TaskType.CHAT,
            title="Minimal Task",
            requirements=TaskRequirements(),
            priority=TaskPriority.LOW,
        )
        scorer = CapabilityScorer()
        result = scorer.score_node(sample_node, task)
        # Score should be >= 0 for an eligible node (may be 0 for minimal requirements)
        assert result.score >= 0


class TestScheduler:
    def test_select_best_node(self, sample_node, sample_task):
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node])
        assert result is not None
        assert result.node_id == "test-node-1"

    def test_select_from_multiple_nodes(self, sample_node, sample_task):
        node2 = NodeResponse(
            node_id="test-node-2",
            hostname="test-02",
            platform=Platform.LINUX,
            architecture=Architecture.X86_64,
            agent_version="0.1.0",
            roles=[NodeRole.WORKER],
            state=NodeState.ONLINE,
            capabilities=NodeCapabilities(
                cpu=CPUCapability(threads=8, architecture=Architecture.X86_64),
                memory=MemoryCapability(
                    total_bytes=32 * 1024**3,
                    available_bytes=16 * 1024**3,
                ),
            ),
            created_at="2024-01-01T00:00:00Z",
        )
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node, node2])
        # sample_node has GPU, node2 doesn't — sample_node should win
        assert result is not None
        assert result.node_id == "test-node-1"

    def test_select_from_multiple_nodes_reverse_order(self, sample_node, sample_task):
        """Test selecting from multiple nodes in reverse order."""
        node2 = NodeResponse(
            node_id="test-node-2",
            hostname="test-02",
            platform=Platform.LINUX,
            architecture=Architecture.X86_64,
            agent_version="0.1.0",
            roles=[NodeRole.WORKER],
            state=NodeState.ONLINE,
            capabilities=NodeCapabilities(
                cpu=CPUCapability(threads=8, architecture=Architecture.X86_64),
                memory=MemoryCapability(
                    total_bytes=32 * 1024**3,
                    available_bytes=16 * 1024**3,
                ),
            ),
            created_at=datetime(2024, 1, 1, 0, 0, 0),
        )
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [node2, sample_node])
        assert result is not None
        assert result.node_id == "test-node-1"

    def test_no_suitable_node(self, sample_node, sample_task):
        sample_node.capabilities.gpus = []
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node])
        assert result is None

    def test_explain_decision(self, sample_node, sample_task):
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node])
        explanation = scheduler.explain_decision(sample_task, result, [sample_node])
        assert "Selected Node" in explanation
        assert "Score" in explanation

    def test_select_from_empty_list(self, sample_task):
        """Test selecting from empty node list."""
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [])
        assert result is None

    def test_select_with_all_offline_nodes(self, sample_node, sample_task):
        """Test selecting when all nodes are offline."""
        sample_node.state = NodeState.OFFLINE
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node])
        assert result is None

    def test_select_prefers_more_capable_node(self, sample_node, sample_task, large_node):
        """Test that scheduler prefers more capable node."""
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node, large_node])
        assert result is not None
        assert result.node_id == "large-node"

    def test_select_with_mixed_states(self, sample_node, sample_task, large_node):
        """Test selecting with mixed node states."""
        sample_node.state = NodeState.OFFLINE
        scheduler = Scheduler()
        result = scheduler.select_node(sample_task, [sample_node, large_node])
        assert result is not None
        assert result.node_id == "large-node"

    def test_scheduler_with_priority_task(self, sample_node, large_node):
        """Test scheduler with high priority task."""
        task = TaskSubmit(
            task_type=TaskType.INFERENCE,
            title="High Priority Task",
            requirements=TaskRequirements(
                cpu_threads=4,
                memory_gb=8,
                gpu_required=True,
                vram_gb=6,
            ),
            priority=TaskPriority.HIGH,
        )
        scheduler = Scheduler()
        result = scheduler.select_node(task, [sample_node, large_node])
        assert result is not None
        # Large node should still win for high priority
        assert result.node_id == "large-node"


class TestSchedulerEdgeCases:
    def test_task_with_zero_requirements(self, sample_node):
        """Test task with zero requirements."""
        task = TaskSubmit(
            task_type=TaskType.CHAT,
            title="Zero Requirements",
            requirements=TaskRequirements(),
            priority=TaskPriority.NORMAL,
        )
        scheduler = Scheduler()
        result = scheduler.select_node(task, [sample_node])
        assert result is not None

    def test_node_with_no_gpu_and_task_no_gpu_requirement(self, sample_node):
        """Test node without GPU when task doesn't need one."""
        sample_node.capabilities.gpus = []
        task = TaskSubmit(
            task_type=TaskType.CHAT,
            title="No GPU Needed",
            requirements=TaskRequirements(
                cpu_threads=2,
                memory_gb=4,
            ),
            priority=TaskPriority.NORMAL,
        )
        scheduler = Scheduler()
        result = scheduler.select_node(task, [sample_node])
        assert result is not None
        assert result.node_id == "test-node-1"
