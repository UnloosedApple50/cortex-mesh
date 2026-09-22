"""
Tests for HermesMesh GPU adapters.
"""

import pytest
from unittest.mock import patch, MagicMock

from hermesmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics
from hermesmesh.adapters.gpu.nvidia import NvidiaGPUAdapter
from hermesmesh.adapters.gpu.amd import AMDGPUAdapter
from hermesmesh.adapters.gpu.intel import IntelGPUAdapter
from hermesmesh.adapters.gpu.apple import AppleGPUAdapter
from hermesmesh.adapters.gpu.generic import GenericGPUAdapter


class TestGPUCapabilities:
    def test_create_capabilities(self):
        caps = GPUCapabilities(
            index=0,
            vendor="nvidia",
            model="RTX 4060",
            vram_bytes=8 * 1024**3,
        )
        assert caps.index == 0
        assert caps.vendor == "nvidia"
        assert caps.vram_bytes == 8 * 1024**3
        assert caps.monitoring_supported is False

    def test_capabilities_defaults(self):
        caps = GPUCapabilities(index=0, vendor="test", model="Test GPU")
        assert caps.driver_version is None
        assert caps.compute_capability is None
        assert caps.pci_bus_id is None


class TestGPUMetrics:
    def test_create_metrics(self):
        m = GPUMetrics(
            index=0,
            model="RTX 4060",
            gpu_usage_percent=45.5,
            memory_used_bytes=4 * 1024**3,
            memory_total_bytes=8 * 1024**3,
            memory_free_bytes=4 * 1024**3,
            temperature_celsius=65.0,
            power_draw_watts=120.0,
        )
        assert m.gpu_usage_percent == 45.5
        assert m.temperature_celsius == 65.0
        assert m.power_draw_watts == 120.0

    def test_metrics_defaults(self):
        m = GPUMetrics(index=0, model="Test")
        assert m.gpu_usage_percent == 0.0
        assert m.temperature_celsius is None


class TestNvidiaGPUAdapter:
    def test_is_available_no_smi(self):
        adapter = NvidiaGPUAdapter()
        # Without nvidia-smi or pynvml, should be False
        # (unless test environment has them)
        assert isinstance(adapter.is_available(), bool)

    def test_detect_returns_list(self):
        adapter = NvidiaGPUAdapter()
        result = adapter.detect()
        assert isinstance(result, list)

    def test_metrics_returns_list(self):
        adapter = NvidiaGPUAdapter()
        result = adapter.metrics()
        assert isinstance(result, list)

    def test_capabilities(self):
        adapter = NvidiaGPUAdapter()
        caps = adapter.capabilities()
        assert "adapter" in caps
        assert "available" in caps

    @patch("hermesmesh.adapters.gpu.nvidia.shutil.which")
    def test_detect_smi_parsing(self, mock_which):
        """Test nvidia-smi output parsing."""
        mock_which.return_value = "/usr/bin/nvidia-smi"
        adapter = NvidiaGPUAdapter()
        # Force non-nvml path
        adapter._nvml = None
        adapter._nvml_available = False
        
        mock_output = "0, NVIDIA GeForce RTX 4060, 8192, GPU-abc123, 12345, 0000:01:00.0\n"
        with patch("hermesmesh.adapters.gpu.base.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result
            
            gpus = adapter._detect_smi()
            assert len(gpus) == 1
            assert gpus[0].model == "NVIDIA GeForce RTX 4060"
            assert gpus[0].vram_bytes == 8192 * 1024 * 1024
            assert gpus[0].uuid == "GPU-abc123"

    @patch("hermesmesh.adapters.gpu.nvidia.shutil.which")
    def test_metrics_smi_parsing(self, mock_which):
        """Test nvidia-smi metrics parsing."""
        mock_which.return_value = "/usr/bin/nvidia-smi"
        adapter = NvidiaGPUAdapter()
        adapter._nvml = None
        adapter._nvml_available = False
        
        mock_output = "0, NVIDIA GeForce RTX 4060, 45.5, 4096, 8192, 4096, 65.0, 120.0, 70, 2505, 7000\n"
        with patch("hermesmesh.adapters.gpu.base.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result
            
            metrics = adapter._metrics_smi()
            assert len(metrics) == 1
            assert metrics[0].gpu_usage_percent == 45.5
            assert metrics[0].temperature_celsius == 65.0
            assert metrics[0].power_draw_watts == 120.0


class TestAMDGPUAdapter:
    def test_is_available(self):
        adapter = AMDGPUAdapter()
        assert isinstance(adapter.is_available(), bool)

    def test_detect_returns_list(self):
        adapter = AMDGPUAdapter()
        result = adapter.detect()
        assert isinstance(result, list)

    def test_metrics_returns_list(self):
        adapter = AMDGPUAdapter()
        result = adapter.metrics()
        assert isinstance(result, list)

    def test_capabilities(self):
        adapter = AMDGPUAdapter()
        caps = adapter.capabilities()
        assert "adapter" in caps


class TestIntelGPUAdapter:
    def test_is_available(self):
        adapter = IntelGPUAdapter()
        assert isinstance(adapter.is_available(), bool)

    def test_detect_returns_list(self):
        adapter = IntelGPUAdapter()
        result = adapter.detect()
        assert isinstance(result, list)

    def test_capabilities(self):
        adapter = IntelGPUAdapter()
        caps = adapter.capabilities()
        assert "adapter" in caps


class TestAppleGPUAdapter:
    def test_is_available_on_apple_silicon(self):
        adapter = AppleGPUAdapter()
        # On Apple arm64, should be True
        # On other systems, False
        result = adapter.is_available()
        assert isinstance(result, bool)

    def test_detect_returns_list(self):
        adapter = AppleGPUAdapter()
        result = adapter.detect()
        assert isinstance(result, list)

    def test_capabilities(self):
        adapter = AppleGPUAdapter()
        caps = adapter.capabilities()
        assert caps.get("api") == "ioreg"
        assert caps.get("unified_memory") is True


class TestGenericGPUAdapter:
    def test_always_available(self):
        adapter = GenericGPUAdapter()
        assert adapter.is_available() is True

    def test_detect_returns_list(self):
        adapter = GenericGPUAdapter()
        result = adapter.detect()
        assert isinstance(result, list)

    def test_metrics_returns_empty(self):
        adapter = GenericGPUAdapter()
        result = adapter.metrics()
        assert result == []

    def test_capabilities(self):
        adapter = GenericGPUAdapter()
        caps = adapter.capabilities()
        assert caps["api"] == "generic"


class TestGPUAdapterBase:
    def test_run_cmd_success(self):
        adapter = GenericGPUAdapter()
        result = adapter._run_cmd(["echo", "hello"])
        assert result == "hello\n"

    def test_run_cmd_failure(self):
        adapter = GenericGPUAdapter()
        result = adapter._run_cmd(["false"])
        assert result is None

    def test_run_cmd_not_found(self):
        adapter = GenericGPUAdapter()
        result = adapter._run_cmd(["/nonexistent/command"])
        assert result is None

    def test_parse_memory_value_mib(self):
        adapter = GenericGPUAdapter()
        result = adapter._parse_memory_value("8192 MiB")
        assert result == 8192 * 1024 * 1024

    def test_parse_memory_value_gib(self):
        adapter = GenericGPUAdapter()
        result = adapter._parse_memory_value("8 GiB")
        assert result == 8 * 1024**3
