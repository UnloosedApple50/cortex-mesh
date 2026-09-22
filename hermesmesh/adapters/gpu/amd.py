"""
HermesMesh — AMD GPU adapter using ROCm and lspci.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from hermesmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics


class AMDGPUAdapter(GPUAdapter):
    """AMD GPU detection via ROCm-smi and lspci fallback."""

    def __init__(self):
        self._rocm_available = False
        try:
            import amdsmi
            amdsmi.amdsmi_init()
            self._amdsmi = amdsmi
            self._rocm_available = True
        except Exception:
            pass

    def is_available(self) -> bool:
        if self._rocm_available:
            return True
        if platform.system() == "Linux":
            if shutil.which("rocm-smi"):
                return True
            if shutil.which("lspci"):
                out = self._run_cmd(["lspci"])
                if out and "AMD" in out and ("VGA" in out or "Display" in out):
                    return True
        return False

    def detect(self) -> List[GPUCapabilities]:
        if self._rocm_available:
            return self._detect_amdsmi()
        if shutil.which("rocm-smi"):
            return self._detect_rocm_smi()
        return self._detect_lspci()

    def metrics(self) -> List[GPUMetrics]:
        if self._rocm_available:
            return self._metrics_amdsmi()
        if shutil.which("rocm-smi"):
            return self._metrics_rocm_smi()
        return []

    def capabilities(self) -> Dict[str, Any]:
        base = super().capabilities()
        base["monitoring"] = True
        if self._rocm_available:
            base["api"] = "AMDSMI"
        elif shutil.which("rocm-smi"):
            base["api"] = "rocm-smi"
        else:
            base["api"] = "lspci"
        return base

    def _detect_amdsmi(self) -> List[GPUCapabilities]:
        gpus = []
        try:
            devices = self._amdsmi.amdsmi_get_device_list()
            for i, dev in enumerate(devices):
                caps = GPUCapabilities(
                    index=i,
                    vendor="amd",
                    model="AMD GPU",
                    monitoring_supported=True,
                )
                try:
                    caps.model = self._amdsmi.amdsmi_get_device_name(dev)
                except Exception:
                    pass
                try:
                    caps.driver_version = self._amdsmi.amdsmi_get_driver_version(dev)
                except Exception:
                    pass
                try:
                    caps.vram_bytes = self._amdsmi.amdsmi_get_device_memory_total(dev)
                except Exception:
                    pass
                gpus.append(caps)
        except Exception:
            pass
        return gpus

    def _detect_rocm_smi(self) -> List[GPUCapabilities]:
        gpus = []
        out = self._run_cmd(["rocm-smi", "--showproductname"])
        if out:
            for i, line in enumerate(out.strip().split("\n")):
                if ":" in line:
                    model = line.split(":")[-1].strip()
                    gpus.append(GPUCapabilities(
                        index=i,
                        vendor="amd",
                        model=model,
                        monitoring_supported=True,
                    ))
        return gpus

    def _detect_lspci(self) -> List[GPUCapabilities]:
        gpus = []
        out = self._run_cmd(["lspci"])
        if not out:
            return gpus
        for line in out.split("\n"):
            if "AMD" in line and ("VGA" in line or "Display" in line):
                model = line.split(":")[-1].strip() if ":" in line else "AMD GPU"
                gpus.append(GPUCapabilities(
                    index=len(gpus),
                    vendor="amd",
                    model=model,
                    monitoring_supported=False,
                ))
        return gpus

    def _metrics_amdsmi(self) -> List[GPUMetrics]:
        metrics = []
        try:
            devices = self._amdsmi.amdsmi_get_device_list()
            for i, dev in enumerate(devices):
                m = GPUMetrics(
                    index=i,
                    model="AMD GPU",
                    monitoring_supported=True,
                )
                try:
                    m.gpu_usage_percent = float(self._amdsmi.amdsmi_get_device_activity(dev))
                except Exception:
                    pass
                try:
                    mem_total = self._amdsmi.amdsmi_get_device_memory_total(dev)
                    mem_used = self._amdsmi.amdsmi_get_device_memory_used(dev)
                    m.memory_total_bytes = int(mem_total)
                    m.memory_used_bytes = int(mem_used)
                    m.memory_free_bytes = int(mem_total - mem_used)
                except Exception:
                    pass
                try:
                    m.temperature_celsius = float(self._amdsmi.amdsmi_get_temp_metric(dev))
                except Exception:
                    pass
                metrics.append(m)
        except Exception:
            pass
        return metrics

    def _metrics_rocm_smi(self) -> List[GPUMetrics]:
        metrics = []
        out = self._run_cmd([
            "rocm-smi", "--showuse", "--showmeminfo", "vram", "--json"
        ])
        if out:
            import json
            try:
                data = json.loads(out)
                for idx_str, gpu_data in data.items():
                    try:
                        idx = int(idx_str)
                    except ValueError:
                        idx = len(metrics)
                    m = GPUMetrics(
                        index=idx,
                        model=gpu_data.get("Card series", "AMD GPU"),
                        gpu_usage_percent=float(gpu_data.get("GPU use (%)", 0)),
                        memory_used_bytes=int(gpu_data.get("VRAM Total Used Memory (B)", 0)),
                        memory_total_bytes=int(gpu_data.get("VRAM Total Memory (B)", 0)),
                    )
                    m.memory_free_bytes = m.memory_total_bytes - m.memory_used_bytes
                    metrics.append(m)
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        return metrics
