"""
Tests for HermesMesh CLI (hermesctl).
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from hermesmesh.cli import app


runner = CliRunner()


class TestCLI:
    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "HermesMesh v0.1.0" in result.output

    def test_doctor(self):
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "HermesMesh Diagnostic" in result.output
        assert "Platform:" in result.output
        assert "CPU:" in result.output
        assert "Memory:" in result.output

    def test_status_no_controller(self):
        """Status without controller should fail."""
        # Ensure env var is not set
        env = os.environ.copy()
        env.pop("HERMESMESH_CONTROLLER", None)
        result = runner.invoke(app, ["status"], env=env)
        assert result.exit_code == 1
        assert "controller" in result.output.lower()

    @patch("httpx.Client")
    def test_status_with_controller(self, mock_client_cls):
        """Status with mocked controller."""
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Mock health response
        mock_health = MagicMock()
        mock_health.json.return_value = {
            "status": "healthy",
            "version": "0.1.0",
        }
        # Mock nodes response
        mock_nodes = MagicMock()
        mock_nodes.json.return_value = [
            {"node_id": "n1", "hostname": "node1", "state": "online"},
            {"node_id": "n2", "hostname": "node2", "state": "offline"},
        ]
        # Mock tasks response
        mock_tasks = MagicMock()
        mock_tasks.json.return_value = [
            {"task_id": "t1", "state": "running"},
            {"task_id": "t2", "state": "queued"},
        ]

        mock_client.get.side_effect = [
            mock_health,
            mock_nodes,
            mock_tasks,
        ]

        result = runner.invoke(
            app, ["status", "--controller", "http://localhost:8000"]
        )
        assert result.exit_code == 0
        assert "Cluster Status" in result.output
        assert "Nodes: 2" in result.output

    def test_node_list_no_controller(self):
        env = os.environ.copy()
        env.pop("HERMESMESH_CONTROLLER", None)
        result = runner.invoke(app, ["node", "list"], env=env)
        assert result.exit_code == 1

    @patch("httpx.Client")
    def test_node_list_empty(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "node",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "No nodes" in result.output

    @patch("httpx.Client")
    def test_node_list_with_nodes(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "node_id": "abc-123",
                "hostname": "node1",
                "state": "online",
                "roles": ["worker"],
            }
        ]
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "node",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "node1" in result.output
        assert "online" in result.output

    @patch("httpx.Client")
    def test_node_info(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "node_id": "abc-123",
            "hostname": "node1",
            "state": "online",
        }
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "node",
                "info",
                "abc-123",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "node1" in result.output

    @patch("httpx.Client")
    def test_node_enable(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.patch.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "node",
                "enable",
                "abc-123",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "enabled" in result.output

    @patch("httpx.Client")
    def test_node_disable(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client.patch.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "node",
                "disable",
                "abc-123",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "disabled" in result.output

    def test_task_list_no_controller(self):
        env = os.environ.copy()
        env.pop("HERMESMESH_CONTROLLER", None)
        result = runner.invoke(app, ["task", "list"], env=env)
        assert result.exit_code == 1

    @patch("httpx.Client")
    def test_task_list_empty(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "task",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "No tasks" in result.output

    @patch("httpx.Client")
    def test_task_submit(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "task_id": "task-123",
            "title": "Test Task",
            "state": "queued",
        }
        mock_client.post.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "task",
                "submit",
                "--title",
                "Test Task",
                "--type",
                "chat",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "task-123" in result.output

    @patch("httpx.Client")
    def test_task_cancel(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": "Cancellation requested"}
        mock_client.post.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "task",
                "cancel",
                "task-123",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "Cancellation requested" in result.output

    @patch("httpx.Client")
    def test_model_list(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "hostname": "node1",
                "capabilities": {
                    "providers": [
                        {
                            "models": ["llama3", "mistral"],
                        }
                    ]
                },
            }
        ]
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "model",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "llama3" in result.output

    @patch("httpx.Client")
    def test_provider_list(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "provider_id": "p1",
                "provider_type": "ollama",
                "name": "Local Ollama",
                "is_available": True,
            }
        ]
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "provider",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "ollama" in result.output

    @patch("httpx.Client")
    def test_event_list(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "event_type": "node_registered",
                "message": "Node registered",
            }
        ]
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "event",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "node_registered" in result.output

    def test_config_show(self):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Configuration" in result.output

    def test_config_set(self):
        result = runner.invoke(
            app, ["config", "set", "test_key", "test_value"]
        )
        assert result.exit_code == 0
        assert "test_key" in result.output

    def test_logs(self):
        result = runner.invoke(app, ["logs"])
        assert result.exit_code == 0
        assert "log" in result.output.lower()

    @patch("httpx.Client")
    def test_storage_list(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "location_id": "loc-1",
                "node_id": "node-1",
                "path": "/data/models",
                "free_bytes": 100 * 1024**3,
            }
        ]
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "storage",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "/data/models" in result.output

    @patch("httpx.Client")
    def test_storage_list_empty(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_client.get.return_value = mock_resp

        result = runner.invoke(
            app,
            [
                "storage",
                "list",
                "--controller",
                "http://localhost:8000",
            ],
        )
        assert result.exit_code == 0
        assert "No storage" in result.output

    @patch("httpx.Client")
    def test_status_connection_error(self, mock_client_cls):
        import httpx
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = runner.invoke(
            app, ["status", "--controller", "http://localhost:9999"]
        )
        assert result.exit_code == 1
        assert "Cannot connect" in result.output

    def test_help_output(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "HermesMesh" in result.output

    def test_version_help(self):
        result = runner.invoke(app, ["version", "--help"])
        assert result.exit_code == 0

    def test_node_help(self):
        result = runner.invoke(app, ["node", "--help"])
        assert result.exit_code == 0

    def test_task_help(self):
        result = runner.invoke(app, ["task", "--help"])
        assert result.exit_code == 0
