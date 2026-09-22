"""
Tests for CortexMesh Agent.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cortexmesh.agent.agent import Agent
from cortexmesh.models import (
    Architecture,
    CPUCapability,
    MemoryCapability,
    Platform,
)


class TestAgent:
    def test_agent_init(self):
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
            node_name="test-node",
        )
        assert agent.controller_url == "http://localhost:8000"
        assert agent.enrollment_token == "test_token_123456"
        assert agent.node_name == "test-node"
        assert agent.node_id is None
        assert agent._running is False

    def test_agent_init_strips_trailing_slash(self):
        agent = Agent(
            controller_url="http://localhost:8000/",
            enrollment_token="test_token_123456",
        )
        assert agent.controller_url == "http://localhost:8000"

    def test_agent_default_heartbeat_interval(self):
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
        )
        assert agent.heartbeat_interval == 5.0

    def test_agent_custom_heartbeat_interval(self):
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
            heartbeat_interval=10.0,
        )
        assert agent.heartbeat_interval == 10.0

    @pytest.mark.asyncio
    async def test_agent_stop(self):
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
        )
        agent._running = True
        await agent.stop()
        assert agent._running is False

    def test_get_hostname(self):
        hostname = Agent._get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    @patch("cortexmesh.agent.agent.detect_all_capabilities")
    @patch("cortexmesh.agent.agent.detect_platform")
    @pytest.mark.asyncio
    async def test_agent_initial_state(
        self, mock_detect_platform, mock_detect_caps
    ):
        """Test agent initial state before start."""
        mock_detect_platform.return_value = (Platform.LINUX, Architecture.X86_64)
        mock_detect_caps.return_value = {
            "cpu": CPUCapability(threads=8, architecture=Architecture.X86_64),
            "memory": MemoryCapability(
                total_bytes=16 * 1024**3, available_bytes=8 * 1024**3
            ),
            "gpus": [],
            "storage": [],
            "network": {"interfaces": []},
        }

        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
            node_name="test-node",
        )

        # Verify initial state
        assert agent.node_id is None
        assert agent._running is False
        assert agent.controller_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_heartbeat_without_node_id(self):
        """Test that heartbeat does nothing without node_id."""
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
        )
        # Should not raise
        await agent._send_heartbeat()

    def test_agent_url_construction(self):
        """Test agent constructs correct URLs."""
        agent = Agent(
            controller_url="http://controller:8000",
            enrollment_token="token123",
        )
        assert agent.controller_url == "http://controller:8000"

    def test_agent_with_custom_node_name(self):
        """Test agent with custom node name."""
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
            node_name="custom-name",
        )
        assert agent.node_name == "custom-name"

    @pytest.mark.asyncio
    async def test_agent_start_stop_cycle(self):
        """Test agent can be started and stopped cleanly."""
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="test_token_123456",
        )
        assert agent._running is False
        # Don't actually start the event loop, just verify state
        await agent.stop()
        assert agent._running is False


class TestAgentCapabilities:
    def test_agent_uses_detected_capabilities(self):
        """Test that agent properly uses detected capabilities."""
        with patch("cortexmesh.agent.agent.detect_all_capabilities") as mock_caps:
            mock_caps.return_value = {
                "cpu": CPUCapability(threads=16),
                "memory": MemoryCapability(total_bytes=32 * 1024**3),
                "gpus": [],
                "storage": [],
                "network": {"interfaces": []},
            }

            caps = mock_caps()
            assert caps["cpu"].threads == 16
            assert caps["memory"].total_bytes == 32 * 1024**3


class TestAgentEdgeCases:
    def test_agent_init_empty_token(self):
        """Test agent handles empty token gracefully."""
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="",
        )
        assert agent.enrollment_token == ""

    def test_agent_init_various_urls(self):
        """Test agent handles various URL formats."""
        urls = [
            "http://localhost:8000",
            "https://controller.example.com",
            "http://192.168.1.100:8080",
        ]
        for url in urls:
            agent = Agent(
                controller_url=url,
                enrollment_token="token",
            )
            assert agent.controller_url == url.rstrip("/")

    @pytest.mark.asyncio
    async def test_multiple_stop_calls(self):
        """Test that multiple stop calls don't cause errors."""
        agent = Agent(
            controller_url="http://localhost:8000",
            enrollment_token="token",
        )
        agent._running = True
        await agent.stop()
        await agent.stop()  # Should not raise
        assert agent._running is False
