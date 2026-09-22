"""
CortexMesh — Platform detection and hardware adapters.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from cortexmesh.models import (
    Architecture, CPUCapability, GPUCapability, GPUVendor,
    MemoryCapability, NetworkCapability, Platform, StorageCapability,
)


def detect_platform() -> Tuple[Platform, Architecture]:
    """Detect current OS and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        os_val = Platform.LINUX
    elif system == "windows":
        os_val = Platform.WINDOWS
    elif system == "darwin":
        os_val = Platform.MACOS
    else:
        os_val = Platform.LINUX  # fallback

    if machine in ("x86_64", "amd64"):
        arch = Architecture.X86_64
    elif machine in ("aarch64", "arm64"):
        arch = Architecture.ARM64
    elif machine.startswith("arm"):
        arch = Architecture.ARM
    else:
        arch = Architecture.UNKNOWN

    return os_val, arch


class CPUAdapter:
    """Detect CPU capabilities."""

    @staticmethod
    def detect() -> CPUCapability:
        caps = CPUCapability()
        _, caps.architecture = detect_platform()

        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    info = f.read()
                model_match = re.search(r"model name\s*:\s*(.+)", info)
                if model_match:
                    caps.model = model_match.group(1).strip()
                cores = re.findall(r"^processor\s*:", info, re.MULTILINE)
                caps.threads = len(cores) if cores else None
                physical = re.findall(r"^physical id\s*:", info, re.MULTILINE)
                caps.sockets = len(set(physical)) if physical else None
                cores_phys = re.findall(r"^cpu cores\s*:\s*(\d+)", info, re.MULTILINE)
                if cores_phys:
                    caps.cores_physical = int(cores_phys[0])

            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    caps.model = result.stdout.strip()
                result = subprocess.run(
                    ["sysctl", "-n", "hw.ncpu"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    caps.threads = int(result.stdout.strip())

            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 3:
                            caps.cores_physical = int(parts[-2])
                            caps.threads = int(parts[-1])

        except Exception:
            pass  # Graceful degradation

        return caps


class MemoryAdapter:
    """Detect memory capabilities."""

    @staticmethod
    def detect() -> MemoryCapability:
        mem = MemoryCapability()

        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    info = f.read()
                total_match = re.search(r"MemTotal:\s+(\d+)", info)
                avail_match = re.search(r"MemAvailable:\s+(\d+)", info)
                swap_total = re.search(r"SwapTotal:\s+(\d+)", info)
                swap_free = re.search(r"SwapFree:\s+(\d+)", info)

                if total_match:
                    mem.total_bytes = int(total_match.group(1)) * 1024
                if avail_match:
                    mem.available_bytes = int(avail_match.group(1)) * 1024
                if swap_total and swap_free:
                    mem.swap_total_bytes = int(swap_total.group(1)) * 1024
                    mem.swap_used_bytes = (
                        int(swap_total.group(1)) - int(swap_free.group(1))
                    ) * 1024

            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    mem.total_bytes = int(result.stdout.strip())

                result = subprocess.run(
                    ["vm_stat"], capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    pages_free = re.search(r"Pages free:\s+(\d+)", result.stdout)
                    if pages_free:
                        mem.available_bytes = int(pages_free.group(1)) * 4096

            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "os", "get", "TotalVisibleMemorySize,FreePhysicalMemory"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 2:
                            mem.total_bytes = int(parts[0]) * 1024
                            mem.available_bytes = int(parts[1]) * 1024

        except Exception:
            pass

        return mem


class GPUAdapter:
    """Detect GPU capabilities."""

    @staticmethod
    def detect() -> List[GPUCapability]:
        gpus = []

        # Try NVIDIA first
        nvidia = GPUAdapter._detect_nvidia()
        if nvidia:
            gpus.extend(nvidia)

        # Try AMD
        amd = GPUAdapter._detect_amd()
        if amd:
            gpus.extend(amd)

        # Try Apple
        apple = GPUAdapter._detect_apple()
        if apple:
            gpus.extend(apple)

        return gpus

    @staticmethod
    def _detect_nvidia() -> List[GPUCapability]:
        gpus = []
        if not shutil.which("nvidia-smi"):
            return gpus

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                 "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        gpu = GPUCapability(
                            vendor=GPUVendor.NVIDIA,
                            model=parts[0],
                            driver_version=parts[2] if len(parts) > 2 else None,
                            monitoring_supported=True,
                        )
                        # Parse VRAM
                        vram_str = parts[1].replace("MiB", "").replace("GiB", "").strip()
                        try:
                            vram = int(vram_str)
                            if "MiB" in parts[1]:
                                gpu.vram_bytes = vram * 1024 * 1024
                            else:
                                gpu.vram_bytes = vram * 1024 * 1024 * 1024
                        except ValueError:
                            pass
                        gpus.append(gpu)
        except Exception:
            pass

        return gpus

    @staticmethod
    def _detect_amd() -> List[GPUCapability]:
        # AMD detection is platform-specific
        # On Linux, check for ROCm or lspci
        gpus = []
        if platform.system() == "Linux" and shutil.which("lspci"):
            try:
                result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "AMD" in line and "VGA" in line:
                            gpus.append(GPUCapability(
                                vendor=GPUVendor.AMD,
                                model=line.split(":")[-1].strip(),
                                monitoring_supported=False,
                            ))
            except Exception:
                pass
        return gpus

    @staticmethod
    def _detect_apple() -> List[GPUCapability]:
        gpus = []
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            gpus.append(GPUCapability(
                vendor=GPUVendor.APPLE,
                model="Apple Silicon GPU",
                monitoring_supported=False,
                enforcement_supported=False,
            ))
        return gpus


class StorageAdapter:
    """Detect storage capabilities."""

    @staticmethod
    def detect() -> List[StorageCapability]:
        storage = []

        try:
            if platform.system() == "Linux":
                result = subprocess.run(
                    ["lsblk", "-J", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    for dev in data.get("blockdevices", []):
                        if dev.get("mountpoint"):
                            # Parse size
                            size_str = dev.get("size", "0")
                            total = StorageAdapter._parse_size(size_str)
                            storage.append(StorageCapability(
                                device=f"/dev/{dev['name']}",
                                mount_point=dev["mountpoint"],
                                filesystem=dev.get("fstype"),
                                total_bytes=total,
                            ))

            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["df", "-k"], capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n")[1:]:
                        parts = line.split()
                        if len(parts) >= 6 and parts[0].startswith("/dev/"):
                            storage.append(StorageCapability(
                                device=parts[0],
                                mount_point=parts[5],
                                total_bytes=int(parts[1]) * 1024,
                                used_bytes=int(parts[2]) * 1024,
                                free_bytes=int(parts[3]) * 1024,
                            ))

        except Exception:
            pass

        return storage

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """Parse size string like '100G' or '500M' to bytes."""
        multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
        match = re.match(r"([\d.]+)\s*([KMGT]?)", size_str.upper())
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return int(value * multipliers.get(unit, 1))
        return 0


class NetworkAdapter:
    """Detect network capabilities."""

    @staticmethod
    def detect() -> NetworkCapability:
        net = NetworkCapability()

        try:
            if platform.system() == "Linux":
                result = subprocess.run(
                    ["ip", "-j", "addr"], capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    import json
                    interfaces = json.loads(result.stdout)
                    for iface in interfaces:
                        name = iface.get("ifname", "")
                        if name == "lo":
                            continue
                        addrs = []
                        for addr_info in iface.get("addr_info", []):
                            addrs.append({
                                "family": addr_info.get("family"),
                                "address": addr_info.get("local"),
                            })
                        if addrs:
                            net.interfaces.append({
                                "name": name,
                                "addresses": addrs,
                            })

            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["ifconfig"], capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    current_iface = None
                    for line in result.stdout.split("\n"):
                        if line and not line.startswith("\t"):
                            current_iface = line.split(":")[0]
                        elif "inet " in line and current_iface:
                            addr = line.split()[1]
                            net.interfaces.append({
                                "name": current_iface,
                                "addresses": [{"family": "inet", "address": addr}],
                            })

        except Exception:
            pass

        return net


def detect_all_capabilities() -> Dict[str, Any]:
    """Run all detection adapters and return complete capabilities."""
    return {
        "cpu": CPUAdapter.detect(),
        "memory": MemoryAdapter.detect(),
        "gpus": GPUAdapter.detect(),
        "storage": StorageAdapter.detect(),
        "network": NetworkAdapter.detect(),
    }
