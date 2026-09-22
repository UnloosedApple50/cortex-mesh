"""
HermesMesh — Apple Silicon GPU adapter using ioreg and Metal.
"""

from __future__ import annotations

import platform
import subprocess
from typing import Any, Dict, List, Optional

from hermesmesh.adapters.gpu.base import GPUAdapter, GPUCapabilities, GPUMetrics


class AppleGPUAdapter(GPUAdapter):
    """Apple Silicon GPU detection via ioreg."""

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    def detect(self) -> List[GPUCapabilities]:
        gpus = []
        if not self.is_available():
            return gpus

        # Try ioreg for Apple Silicon
        out = self._run_cmd([
            "ioreg", "-l", "-w0", "-p", "IOService",
            "-n", "AGX"
        ])
        if not out:
            out = self._run_cmd([
                "ioreg", "-l", "-w0", "-p", "IOService",
                "-n", "AppleARMIODevice"
            ])

        if out:
            # Parse ioreg output for GPU info
            model = "Apple Silicon GPU"
            if "AGX" in out:
                # Try to extract chip variant
                for line in out.split("\n"):
                    if "model" in line.lower() and ">" in line:
                        model = line.split(">")[-1].strip().strip('"')
                        break
            gpus.append(GPUCapabilities(
                index=0,
                vendor="apple",
                model=model,
                monitoring_supported=False,  # Apple doesn't expose GPU metrics easily
                enforcement_supported=False,
            ))
        else:
            # Fallback: just report Apple Silicon
            gpus.append(GPUCapabilities(
                index=0,
                vendor="apple",
                model="Apple Silicon GPU",
                monitoring_supported=False,
                enforcement_supported=False,
            ))

        return gpus

    def metrics(self) -> List[GPUMetrics]:
        # Apple doesn't expose real-time GPU metrics via CLI
        # Return empty metrics
        return []

    def capabilities(self) -> Dict[str, Any]:
        base = super().capabilities()
        base["api"] = "ioreg"
        base["unified_memory"] = True
        return base
