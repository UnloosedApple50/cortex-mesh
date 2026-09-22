"""
HermesMesh — Intel GPU adapter using Level Zero and lspci.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from hermesmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics


class IntelGPUAdapter(GPUAdapter):
    """Intel GPU detection via Level Zero and lspci fallback."""

    def __init__(self):
        self._level_zero = None
        try:
            import zeep as ze  # level_zero Python bindings placeholder
            self._level_zero = ze
        except Exception:
            pass

    def is_available(self) -> bool:
        if self._level_zero:
            return True
        if platform.system() == "Linux" and shutil.which("lspci"):
            out = self._run_cmd(["lspci"])
            if out and "Intel" in out and ("VGA" in out or "Display" in out):
                return True
        if shutil.which("xpu-smi"):
            return True
        return False

    def detect(self) -> List[GPUCapabilities]:
        gpus = []
        if self._level_zero:
            gpus = self._detect_level_zero()
        elif shutil.which("xpu-smi"):
            gpus = self._detect_xpu_smi()
        else:
            gpus = self._detect_lspci()
        return gpus

    def metrics(self) -> List[GPUMetrics]:
        if shutil.which("xpu-smi"):
            return self._metrics_xpu_smi()
        return []

    def capabilities(self) -> Dict[str, Any]:
        base = super().capabilities()
        base["monitoring"] = bool(shutil.which("xpu-smi"))
        if self._level_zero:
            base["api"] = "Level Zero"
        elif shutil.which("xpu-smi"):
            base["api"] = "xpu-smi"
        else:
            base["api"] = "lspci"
        return base

    def _detect_level_zero(self) -> List[GPUCapabilities]:
        gpus = []
        try:
            devices = self._level_zero.get_devices()
            for i, dev in enumerate(devices):
                props = dev.get_properties()
                gpus.append(GPUCapabilities(
                    index=i,
                    vendor="intel",
                    model=props.get("name", "Intel GPU"),
                    vram_bytes=props.get("globalMemSize"),
                    monitoring_supported=True,
                ))
        except Exception:
            pass
        return gpus

    def _detect_xpu_smi(self) -> List[GPUCapabilities]:
        gpus = []
        out = self._run_cmd(["xpu-smi", "discovery", "--json"])
        if out:
            import json
            try:
                data = json.loads(out)
                for i, gpu in enumerate(data.get("gpu_devices", [])):
                    gpus.append(GPUCapabilities(
                        index=i,
                        vendor="intel",
                        model=gpu.get("device_name", "Intel GPU"),
                        driver_version=gpu.get("driver_version"),
                        monitoring_supported=True,
                    ))
            except (json.JSONDecodeError, KeyError):
                pass
        return gpus

    def _detect_lspci(self) -> List[GPUCapabilities]:
        gpus = []
        out = self._run_cmd(["lspci"])
        if not out:
            return gpus
        for line in out.split("\n"):
            if "Intel" in line and ("VGA" in line or "Display" in line):
                model = line.split(":")[-1].strip() if ":" in line else "Intel GPU"
                gpus.append(GPUCapabilities(
                    index=len(gpus),
                    vendor="intel",
                    model=model,
                    monitoring_supported=False,
                ))
        return gpus

    def _metrics_xpu_smi(self) -> List[GPUMetrics]:
        metrics = []
        out = self._run_cmd(["xpu-smi", "dump", "--json"])
        if out:
            import json
            try:
                data = json.loads(out)
                for i, gpu_data in enumerate(data):
                    m = GPUMetrics(
                        index=i,
                        model=gpu_data.get("device_name", "Intel GPU"),
                    )
                    # Parse metrics from dump output
                    for stat in gpu_data.get("stats", []):
                        name = stat.get("name", "")
                        value = stat.get("value", 0)
                        if "utilization" in name.lower():
                            m.gpu_usage_percent = float(value)
                        elif "memory_used" in name.lower():
                            m.memory_used_bytes = int(float(value))
                        elif "memory_total" in name.lower():
                            m.memory_total_bytes = int(float(value))
                        elif "temperature" in name.lower():
                            m.temperature_celsius = float(value)
                    if m.memory_total_bytes > 0:
                        m.memory_free_bytes = m.memory_total_bytes - m.memory_used_bytes
                    metrics.append(m)
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        return metrics
