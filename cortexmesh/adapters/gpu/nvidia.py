"""
CortexMesh — NVIDIA GPU adapter using NVML (pynvml) and nvidia-smi fallback.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from cortexmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics


class NvidiaGPUAdapter(GPUAdapter):
    """NVIDIA GPU detection via nvidia-smi and optionally NVML."""

    def __init__(self):
        self._nvml = None
        self._nvml_available = False
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml = pynvml
            self._nvml_available = True
        except Exception:
            pass

    def is_available(self) -> bool:
        if self._nvml_available:
            return True
        return shutil.which("nvidia-smi") is not None

    def detect(self) -> List[GPUCapabilities]:
        if self._nvml_available:
            return self._detect_nvml()
        return self._detect_smi()

    def metrics(self) -> List[GPUMetrics]:
        if self._nvml_available:
            return self._metrics_nvml()
        return self._metrics_smi()

    def capabilities(self) -> Dict[str, Any]:
        base = super().capabilities()
        base["monitoring"] = True
        base["enforcement"] = False  # NVIDIA doesn't expose enforcement APIs easily
        if self._nvml_available:
            base["api"] = "NVML"
            try:
                base["driver_version"] = self._nvml.nvmlSystemGetDriverVersion()
                base["nvml_version"] = self._nvml.nvmlSystemGetNVMLVersion()
            except Exception:
                pass
        else:
            base["api"] = "nvidia-smi"
            out = self._run_cmd(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
            if out:
                base["driver_version"] = out.strip().split("\n")[0]
        return base

    def _detect_nvml(self) -> List[GPUCapabilities]:
        gpus = []
        try:
            count = self._nvml.nvmlDeviceGetCount()
            for i in range(count):
                handle = self._nvml.nvmlDeviceGetHandleByIndex(i)
                name = self._nvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode()
                mem_info = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                caps = GPUCapabilities(
                    index=i,
                    vendor="nvidia",
                    model=name,
                    vram_bytes=mem_info.total,
                    monitoring_supported=True,
                )
                try:
                    caps.compute_capability = self._nvml.nvmlDeviceGetCudaComputeCapability(handle)
                    caps.compute_capability = f"{caps.compute_capability[0]}.{caps.compute_capability[1]}"
                except Exception:
                    pass
                try:
                    caps.uuid = self._nvml.nvmlDeviceGetUUID(handle)
                    if isinstance(caps.uuid, bytes):
                        caps.uuid = caps.uuid.decode()
                except Exception:
                    pass
                try:
                    caps.serial = self._nvml.nvmlDeviceGetSerial(handle)
                    if isinstance(caps.serial, bytes):
                        caps.serial = caps.serial.decode()
                except Exception:
                    pass
                gpus.append(caps)
        except Exception:
            pass
        return gpus

    def _detect_smi(self) -> List[GPUCapabilities]:
        gpus = []
        query = [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,uuid,serial,pci.bus_id",
            "--format=csv,noheader,nounits",
        ]
        out = self._run_cmd(query)
        if not out:
            return gpus
        for line in out.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                try:
                    idx = int(parts[0])
                    model = parts[1]
                    vram = int(float(parts[2]) * 1024 * 1024)  # MiB to bytes
                    caps = GPUCapabilities(
                        index=idx,
                        vendor="nvidia",
                        model=model,
                        vram_bytes=vram,
                        uuid=parts[3] if len(parts) > 3 else None,
                        serial=parts[4] if len(parts) > 4 else None,
                        pci_bus_id=parts[5] if len(parts) > 5 else None,
                        monitoring_supported=True,
                    )
                    gpus.append(caps)
                except (ValueError, IndexError):
                    continue
        return gpus

    def _metrics_nvml(self) -> List[GPUMetrics]:
        metrics = []
        try:
            count = self._nvml.nvmlDeviceGetCount()
            for i in range(count):
                handle = self._nvml.nvmlDeviceGetHandleByIndex(i)
                name = self._nvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode()
                util = self._nvml.nvmlDeviceGetUtilizationRates(handle)
                mem = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                m = GPUMetrics(
                    index=i,
                    model=name,
                    gpu_usage_percent=float(util.gpu),
                    memory_used_bytes=mem.used,
                    memory_total_bytes=mem.total,
                    memory_free_bytes=mem.free,
                )
                try:
                    m.temperature_celsius = float(
                        self._nvml.nvmlDeviceGetTemperature(handle, self._nvml.NVML_TEMPERATURE_GPU)
                    )
                except Exception:
                    pass
                try:
                    m.power_draw_watts = float(
                        self._nvml.nvmlDeviceGetPowerUsage(handle)
                    ) / 1000.0
                except Exception:
                    pass
                try:
                    m.clock_sm_mhz = int(self._nvml.nvmlDeviceGetClockInfo(handle, self._nvml.NVML_CLOCK_SM))
                    m.clock_memory_mhz = int(self._nvml.nvmlDeviceGetClockInfo(handle, self._nvml.NVML_CLOCK_MEM))
                except Exception:
                    pass
                metrics.append(m)
        except Exception:
            pass
        return metrics

    def _metrics_smi(self) -> List[GPUMetrics]:
        metrics = []
        query = [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,memory.free,"
            "temperature.power,power.draw,fan.speed,clocks.sm,clocks.mem",
            "--format=csv,noheader,nounits",
        ]
        out = self._run_cmd(query)
        if not out:
            return metrics
        for line in out.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                try:
                    m = GPUMetrics(
                        index=int(parts[0]),
                        model=parts[1],
                        gpu_usage_percent=float(parts[2]),
                        memory_used_bytes=int(float(parts[3]) * 1024 * 1024),
                        memory_total_bytes=int(float(parts[4]) * 1024 * 1024),
                        memory_free_bytes=int(float(parts[5]) * 1024 * 1024),
                    )
                    if len(parts) > 6 and parts[6] != "[N/A]":
                        m.temperature_celsius = float(parts[6])
                    if len(parts) > 7 and parts[7] != "[N/A]":
                        m.power_draw_watts = float(parts[7])
                    if len(parts) > 8 and parts[8] != "[N/A]":
                        m.fan_speed_percent = float(parts[8])
                    if len(parts) > 9 and parts[9] != "[N/A]":
                        m.clock_sm_mhz = int(float(parts[9]))
                    if len(parts) > 10 and parts[10] != "[N/A]":
                        m.clock_memory_mhz = int(float(parts[10]))
                    metrics.append(m)
                except (ValueError, IndexError):
                    continue
        return metrics
