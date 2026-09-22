"""
CortexMesh — Generic fallback GPU adapter.

Used when no vendor-specific adapter is available.
Tries basic system commands to detect any GPU.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from cortexmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics


class GenericGPUAdapter(GPUAdapter):
    """Generic GPU detection fallback."""

    def is_available(self) -> bool:
        # Always available as fallback
        return True

    def detect(self) -> List[GPUCapabilities]:
        gpus = []

        if platform.system() == "Linux":
            # Try lspci for any VGA device
            if shutil.which("lspci"):
                out = self._run_cmd(["lspci"])
                if out:
                    for line in out.split("\n"):
                        if "VGA" in line or "3D" in line or "Display" in line:
                            model = line.split(":")[-1].strip() if ":" in line else "Unknown GPU"
                            vendor = "unknown"
                            if "NVIDIA" in line:
                                vendor = "nvidia"
                            elif "AMD" in line or "ATI" in line:
                                vendor = "amd"
                            elif "Intel" in line:
                                vendor = "intel"
                            gpus.append(GPUCapabilities(
                                index=len(gpus),
                                vendor=vendor,
                                model=model,
                                monitoring_supported=False,
                            ))

            # Try to get more info from /sys
            if not gpus:
                out = self._run_cmd(["find", "/sys/class/drm", "-name", "device", "-type", "l"])
                if out:
                    for dev_path in out.strip().split("\n"):
                        dev_name = dev_path.split("/")[-2] if dev_path else "unknown"
                        gpus.append(GPUCapabilities(
                            index=len(gpus),
                            vendor="unknown",
                            model=f"DRM Device ({dev_name})",
                            monitoring_supported=False,
                        ))

        elif platform.system() == "Darwin":
            # macOS: check system_profiler
            out = self._run_cmd(["system_profiler", "SPDisplaysDataType"])
            if out:
                for line in out.split("\n"):
                    if "Chipset Model:" in line:
                        model = line.split(":")[-1].strip()
                        vendor = "unknown"
                        if "Apple" in model:
                            vendor = "apple"
                        elif "Intel" in model:
                            vendor = "intel"
                        gpus.append(GPUCapabilities(
                            index=len(gpus),
                            vendor=vendor,
                            model=model,
                            monitoring_supported=False,
                        ))

        elif platform.system() == "Windows":
            # Try wmic
            out = self._run_cmd(["wmic", "path", "win32_VideoController", "get", "Name"])
            if out:
                for line in out.strip().split("\n")[1:]:
                    model = line.strip()
                    if model:
                        vendor = "unknown"
                        if "NVIDIA" in model:
                            vendor = "nvidia"
                        elif "AMD" in model or "Radeon" in model:
                            vendor = "amd"
                        elif "Intel" in model:
                            vendor = "intel"
                        gpus.append(GPUCapabilities(
                            index=len(gpus),
                            vendor=vendor,
                            model=model,
                            monitoring_supported=False,
                        ))

        return gpus

    def metrics(self) -> List[GPUMetrics]:
        # Generic adapter can't provide metrics
        return []

    def capabilities(self) -> Dict[str, Any]:
        base = super().capabilities()
        base["api"] = "generic"
        base["note"] = "Limited detection, no metrics"
        return base
