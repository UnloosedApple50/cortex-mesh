"""
HermesMesh — GPU adapters package.

Provides unified GPU detection and monitoring across vendors.
"""

from __future__ import annotations

import platform
from typing import Any, Dict, List, Optional

from hermesmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics
from hermesmesh.adapters.gpu.nvidia import NvidiaGPUAdapter
from hermesmesh.adapters.gpu.amd import AMDGPUAdapter
from hermesmesh.adapters.gpu.intel import IntelGPUAdapter
from hermesmesh.adapters.gpu.apple import AppleGPUAdapter
from hermesmesh.adapters.gpu.generic import GenericGPUAdapter


def get_gpu_adapters() -> List[GPUAdapter]:
    """Get all available GPU adapters for this system."""
    adapters = []

    # Try vendor-specific adapters first
    nvidia = NvidiaGPUAdapter()
    if nvidia.is_available():
        adapters.append(nvidia)

    amd = AMDGPUAdapter()
    if amd.is_available():
        adapters.append(amd)

    intel = IntelGPUAdapter()
    if intel.is_available():
        adapters.append(intel)

    apple = AppleGPUAdapter()
    if apple.is_available():
        adapters.append(apple)

    # Always add generic as fallback
    generic = GenericGPUAdapter()
    adapters.append(generic)

    return adapters


def detect_all_gpus() -> List[GPUCapabilities]:
    """Detect all GPUs using available adapters."""
    all_gpus = []
    for adapter in get_gpu_adapters():
        try:
            gpus = adapter.detect()
            all_gpus.extend(gpus)
        except Exception:
            continue
    return all_gpus


def get_all_metrics() -> List[GPUMetrics]:
    """Get metrics from all available adapters."""
    all_metrics = []
    for adapter in get_gpu_adapters():
        try:
            metrics = adapter.metrics()
            all_metrics.extend(metrics)
        except Exception:
            continue
    return all_metrics


def get_adapter_capabilities() -> Dict[str, Any]:
    """Get capabilities of all available adapters."""
    caps = {}
    for adapter in get_gpu_adapters():
        name = adapter.__class__.__name__
        try:
            caps[name] = adapter.capabilities()
        except Exception:
            caps[name] = {"error": "Failed to get capabilities"}
    return caps


__all__ = [
    "GPUAdapter",
    "GPUCapabilities",
    "GPUMetrics",
    "NvidiaGPUAdapter",
    "AMDGPUAdapter",
    "IntelGPUAdapter",
    "AppleGPUAdapter",
    "GenericGPUAdapter",
    "get_gpu_adapters",
    "detect_all_gpus",
    "get_all_metrics",
    "get_adapter_capabilities",
]
