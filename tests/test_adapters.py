"""
Tests for CortexMesh platform detection.
"""

import pytest
from cortexmesh.adapters.platform.detect import (
    CPUAdapter, MemoryAdapter, GPUAdapter, StorageAdapter,
    NetworkAdapter, detect_platform, detect_all_capabilities,
)
from cortexmesh.models import Platform, Architecture


class TestPlatformDetection:
    def test_detect_platform_returns_valid(self):
        platform, arch = detect_platform()
        assert isinstance(platform, Platform)
        assert isinstance(arch, Architecture)

    def test_detect_all_capabilities(self):
        caps = detect_all_capabilities()
        assert "cpu" in caps
        assert "memory" in caps
        assert "gpus" in caps
        assert "storage" in caps
        assert "network" in caps


class TestCPUAdapter:
    def test_detect_returns_capabilities(self):
        caps = CPUAdapter.detect()
        assert caps.architecture in (Architecture.X86_64, Architecture.ARM64, Architecture.ARM)
        # At least some info should be available
        assert caps.threads is not None or caps.model is not None


class TestMemoryAdapter:
    def test_detect_returns_memory(self):
        mem = MemoryAdapter.detect()
        assert mem.total_bytes > 0
        assert mem.available_bytes >= 0


class TestGPUAdapter:
    def test_detect_returns_list(self):
        gpus = GPUAdapter.detect()
        assert isinstance(gpus, list)


class TestStorageAdapter:
    def test_detect_returns_list(self):
        storage = StorageAdapter.detect()
        assert isinstance(storage, list)


class TestNetworkAdapter:
    def test_detect_returns_network(self):
        net = NetworkAdapter.detect()
        assert isinstance(net.interfaces, list)
