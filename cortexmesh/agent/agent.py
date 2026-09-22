"""
CortexMesh — Enhanced Agent with reconnection, capability refresh, and metric reporting.
"""

from __future__ import annotations

import asyncio
import json
import socket
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from cortexmesh.adapters.platform.detect import detect_all_capabilities, detect_platform
from cortexmesh.adapters.gpu import get_all_metrics, detect_all_gpus
from cortexmesh.models import (
    Architecture, NodeRegisterRequest, NodeRole, Platform,
    NodeCapabilities, CPUCapability, MemoryCapability,
)


class Agent:
    """
    CortexMesh Agent runs on each node.

    Responsibilities:
    - Detect hardware capabilities
    - Register with controller
    - Send heartbeats with metrics
    - Reconnect with exponential backoff
    - Refresh capabilities periodically
    - Graceful shutdown
    """

    def __init__(
        self,
        controller_url: str,
        enrollment_token: str,
        node_name: Optional[str] = None,
        heartbeat_interval: float = 5.0,
        max_reconnect_delay: float = 60.0,
        capability_refresh_interval: float = 300.0,
    ):
        self.controller_url = controller_url.rstrip("/")
        self.enrollment_token = enrollment_token
        self.node_name = node_name
        self.heartbeat_interval = heartbeat_interval
        self.max_reconnect_delay = max_reconnect_delay
        self.capability_refresh_interval = capability_refresh_interval
        self.node_id: Optional[str] = None
        self._http: Optional[httpx.AsyncClient] = None
        self._running = False
        self._reconnect_delay = 1.0
        self._last_capability_refresh: Optional[datetime] = None
        self._capabilities: Optional[NodeCapabilities] = None
        self._metrics_history: List[Dict[str, Any]] = []

    async def start(self):
        """Start the agent with reconnection support."""
        self._running = True
        
        # Create HTTP client if not already set (allows injection for testing)
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10.0)

        while self._running:
            try:
                await self._register()
                self._reconnect_delay = 1.0  # Reset on success
                await self._run_main_loop()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                print(f"Connection error: {e}. Retrying in {self._reconnect_delay:.1f}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self.max_reconnect_delay
                )

        await self._cleanup()

    async def stop(self):
        """Gracefully stop the agent."""
        self._running = False
        await self._cleanup()

    async def _cleanup(self):
        """Clean up resources."""
        if self._http:
            await self._http.aclose()
            self._http = None

    async def _register(self):
        """Register with the controller."""
        platform_val, arch_val = detect_platform()
        caps = self._detect_capabilities()

        req = NodeRegisterRequest(
            enrollment_token=self.enrollment_token,
            hostname=self.node_name or self._get_hostname(),
            platform=platform_val,
            architecture=arch_val,
            agent_version="0.1.0",
            capabilities=caps,
            roles=[NodeRole.WORKER],
        )

        resp = await self._http.post(
            f"{self.controller_url}/api/v1/nodes/register",
            json=req.model_dump(),
        )
        resp.raise_for_status()
        data = resp.json()
        self.node_id = data["node_id"]
        print(f"Registered as node: {self.node_id}")

    def _detect_capabilities(self) -> NodeCapabilities:
        """Detect all capabilities including GPU."""
        caps = detect_all_capabilities()

        # Enhance with GPU adapter data
        try:
            gpu_caps = detect_all_gpus()
            from cortexmesh.models import GPUCapability, GPUVendor
            for gc in gpu_caps:
                vendor_map = {
                    "nvidia": GPUVendor.NVIDIA,
                    "amd": GPUVendor.AMD,
                    "intel": GPUVendor.INTEL,
                    "apple": GPUVendor.APPLE,
                }
                caps["gpus"].append(GPUCapability(
                    vendor=vendor_map.get(gc.vendor, GPUVendor.UNKNOWN),
                    model=gc.model,
                    vram_bytes=gc.vram_bytes,
                    driver_version=gc.driver_version,
                    compute_capability=gc.compute_capability,
                    monitoring_supported=gc.monitoring_supported,
                    enforcement_supported=gc.enforcement_supported,
                ))
        except Exception:
            pass

        self._capabilities = NodeCapabilities(**caps)
        self._last_capability_refresh = datetime.now(timezone.utc)
        return self._capabilities

    async def _run_main_loop(self):
        """Main loop: heartbeats + capability refresh."""
        while self._running:
            try:
                # Check if capabilities need refresh
                if self._should_refresh_capabilities():
                    await self._refresh_capabilities()

                # Send heartbeat with metrics
                await self._send_heartbeat()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Node was deleted, re-register
                    print("Node not found, re-registering...")
                    self.node_id = None
                    raise  # Will trigger reconnection
                print(f"HTTP error: {e}")
            except httpx.ConnectError:
                raise  # Trigger reconnection
            except Exception as e:
                print(f"Heartbeat error: {e}")

            await asyncio.sleep(self.heartbeat_interval)

    def _should_refresh_capabilities(self) -> bool:
        """Check if capabilities should be refreshed."""
        if self._last_capability_refresh is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self._last_capability_refresh).total_seconds()
        return elapsed >= self.capability_refresh_interval

    async def _refresh_capabilities(self):
        """Refresh and report updated capabilities."""
        caps = self._detect_capabilities()
        if self.node_id and self._http:
            try:
                resp = await self._http.post(
                    f"{self.controller_url}/api/v1/nodes/{self.node_id}/capabilities",
                    json=caps.model_dump(),
                )
                if resp.status_code == 200:
                    print("Capabilities refreshed")
            except Exception as e:
                print(f"Failed to refresh capabilities: {e}")

    async def _send_heartbeat(self):
        """Send heartbeat with current metrics."""
        if not self.node_id or not self._http:
            return

        metrics = self._collect_metrics()
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": "online",
            **metrics,
        }

        resp = await self._http.post(
            f"{self.controller_url}/api/v1/nodes/{self.node_id}/heartbeat",
            json=payload,
        )
        resp.raise_for_status()

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        metrics = {
            "cpu_usage_percent": self._get_cpu_usage(),
            "memory_usage_percent": self._get_memory_usage(),
            "gpu_usage_percent": None,
            "storage_usage_percent": None,
            "tasks_running": 0,
        }

        # GPU metrics
        try:
            gpu_metrics = get_all_metrics()
            if gpu_metrics:
                avg_gpu = sum(m.gpu_usage_percent for m in gpu_metrics) / len(gpu_metrics)
                metrics["gpu_usage_percent"] = avg_gpu
                metrics["gpu_details"] = [
                    {
                        "index": m.index,
                        "model": m.model,
                        "usage": m.gpu_usage_percent,
                        "memory_used": m.memory_used_bytes,
                        "memory_total": m.memory_total_bytes,
                        "temperature": m.temperature_celsius,
                    }
                    for m in gpu_metrics
                ]
        except Exception:
            pass

        # Store in history
        self._metrics_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **metrics,
        })
        # Keep only last 100 entries
        if len(self._metrics_history) > 100:
            self._metrics_history = self._metrics_history[-100:]

        return metrics

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            pass
        try:
            # Fallback for Linux
            with open("/proc/stat") as f:
                line = f.readline()
            fields = line.split()
            if fields[0] == "cpu":
                idle = int(fields[4])
                total = sum(int(f) for f in fields[1:])
                if total > 0:
                    return 100.0 * (1.0 - idle / total)
        except Exception:
            pass
        return 0.0

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            pass
        try:
            # Fallback for Linux
            with open("/proc/meminfo") as f:
                info = f.read()
            import re
            total = re.search(r"MemTotal:\\s+(\\d+)", info)
            avail = re.search(r"MemAvailable:\\s+(\\d+)", info)
            if total and avail:
                t = int(total.group(1))
                a = int(avail.group(1))
                if t > 0:
                    return 100.0 * (1.0 - a / t)
        except Exception:
            pass
        return 0.0

    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get recent metrics history."""
        return list(self._metrics_history)

    @staticmethod
    def _get_hostname() -> str:
        return socket.gethostname()
