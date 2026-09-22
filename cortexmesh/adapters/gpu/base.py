"""
CortexMesh — GPU Adapter base class.

Each GPU vendor adapter implements detect(), metrics(), and capabilities().
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GPUMetrics:
    """Real-time metrics for a single GPU."""
    index: int
    model: str
    gpu_usage_percent: float = 0.0
    memory_used_bytes: int = 0
    memory_total_bytes: int = 0
    memory_free_bytes: int = 0
    temperature_celsius: Optional[float] = None
    power_draw_watts: Optional[float] = None
    fan_speed_percent: Optional[float] = None
    clock_sm_mhz: Optional[int] = None
    clock_memory_mhz: Optional[int] = None


@dataclass
class GPUCapabilities:
    """Static capabilities of a GPU."""
    index: int
    vendor: str
    model: str
    vram_bytes: Optional[int] = None
    driver_version: Optional[str] = None
    compute_capability: Optional[str] = None
    pci_bus_id: Optional[str] = None
    serial: Optional[str] = None
    uuid: Optional[str] = None
    monitoring_supported: bool = False
    enforcement_supported: bool = False


class GPUAdapter(ABC):
    """Abstract base for GPU detection and monitoring adapters."""

    @abstractmethod
    def detect(self) -> List[GPUCapabilities]:
        """Detect GPUs available on this system."""
        ...

    @abstractmethod
    def metrics(self) -> List[GPUMetrics]:
        """Get real-time metrics for all detected GPUs."""
        ...

    def capabilities(self) -> Dict[str, Any]:
        """Return adapter capabilities metadata."""
        return {
            "adapter": self.__class__.__name__,
            "available": self.is_available(),
            "monitoring": False,
            "enforcement": False,
        }

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this GPU adapter can be used on this system."""
        ...

    @staticmethod
    def _run_cmd(cmd: List[str], timeout: int = 10) -> Optional[str]:
        """Run a command and return stdout, or None on failure."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return None

    @staticmethod
    def _parse_memory_value(value_str: str) -> Optional[int]:
        """Parse a memory string like '8192 MiB' or '16 GiB' to bytes."""
        match = re.match(r"([\d.]+)\s*(MiB|GiB|KiB|MB|GB|KB)?", value_str.strip())
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2) or "MiB"
        multipliers = {
            "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
            "KB": 1000, "MB": 1000**2, "GB": 1000**3,
        }
        return int(value * multipliers.get(unit, 1024**2))
