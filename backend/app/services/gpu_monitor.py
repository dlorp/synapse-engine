"""GPU monitoring utilities.

This module provides cross-platform GPU metrics collection, supporting:
- NVIDIA GPUs (via nvidia-smi)
- Apple Silicon (unified memory reporting)
- Graceful fallback for systems without GPU

The module caches GPU detection results to minimize subprocess overhead.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information container."""

    name: str
    memory_used_gb: float
    memory_total_gb: float
    memory_percent: float
    is_unified_memory: bool = False  # True for Apple Silicon
    gpu_utilization: Optional[float] = None  # GPU compute utilization %


# Cache for GPU detection
_cached_gpu_type: Optional[str] = None  # "nvidia", "apple_silicon", "none"


def _detect_gpu_type() -> str:
    """Detect available GPU type.

    Returns:
        "nvidia" for NVIDIA GPUs
        "apple_silicon" for Apple Silicon Macs
        "none" for no GPU or unsupported GPU
    """
    global _cached_gpu_type
    if _cached_gpu_type is not None:
        return _cached_gpu_type

    # Check for NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            _cached_gpu_type = "nvidia"
            logger.info(f"Detected NVIDIA GPU: {result.stdout.strip()}")
            return _cached_gpu_type
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Check for Apple Silicon
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                cpu_brand = result.stdout.strip().lower()
                if "apple" in cpu_brand or any(
                    chip in cpu_brand for chip in ["m1", "m2", "m3", "m4"]
                ):
                    _cached_gpu_type = "apple_silicon"
                    logger.info(f"Detected Apple Silicon: {result.stdout.strip()}")
                    return _cached_gpu_type
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        # Alternative detection via uname
        try:
            result = subprocess.run(["uname", "-m"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip() == "arm64":
                _cached_gpu_type = "apple_silicon"
                logger.info("Detected Apple Silicon via arm64 architecture")
                return _cached_gpu_type
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    _cached_gpu_type = "none"
    logger.info("No supported GPU detected")
    return _cached_gpu_type


def _get_nvidia_metrics() -> Optional[GPUInfo]:
    """Get NVIDIA GPU metrics via nvidia-smi.

    Returns:
        GPUInfo if successful, None otherwise
    """
    try:
        # Query GPU name, memory used, memory total, and utilization
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        # Parse CSV output (handles multi-GPU by taking first)
        line = result.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]

        if len(parts) >= 4:
            name = parts[0]
            memory_used_mb = float(parts[1])
            memory_total_mb = float(parts[2])
            gpu_util = float(parts[3])

            memory_used_gb = memory_used_mb / 1024
            memory_total_gb = memory_total_mb / 1024
            memory_percent = (memory_used_mb / memory_total_mb * 100) if memory_total_mb > 0 else 0

            return GPUInfo(
                name=name,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                memory_percent=memory_percent,
                gpu_utilization=gpu_util,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError, ValueError) as e:
        logger.debug(f"Failed to get NVIDIA metrics: {e}")

    return None


def _get_apple_silicon_metrics() -> Optional[GPUInfo]:
    """Get Apple Silicon unified memory metrics.

    On Apple Silicon, GPU memory is part of the unified memory pool.
    We report system memory as it's shared with the GPU.

    Returns:
        GPUInfo with unified memory stats
    """
    try:
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        memory_percent = memory.percent

        # Detect chip model for name
        chip_name = "Apple Silicon GPU"
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                chip_name = f"{result.stdout.strip()} GPU (Unified Memory)"
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        return GPUInfo(
            name=chip_name,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            memory_percent=memory_percent,
            is_unified_memory=True,
            gpu_utilization=None,  # Not easily available on macOS
        )
    except Exception as e:
        logger.debug(f"Failed to get Apple Silicon metrics: {e}")

    return None


def get_gpu_metrics() -> Tuple[float, float, float, Optional[str]]:
    """Get GPU memory metrics.

    Cross-platform GPU memory collection:
    - NVIDIA: Real VRAM usage via nvidia-smi
    - Apple Silicon: Unified memory (shared with CPU)
    - Other: Returns zeros

    Returns:
        Tuple of (memory_used_gb, memory_total_gb, memory_percent, gpu_name)
        Returns (0.0, 0.0, 0.0, None) if no GPU or error
    """
    gpu_type = _detect_gpu_type()

    if gpu_type == "nvidia":
        info = _get_nvidia_metrics()
        if info:
            return (
                info.memory_used_gb,
                info.memory_total_gb,
                info.memory_percent,
                info.name,
            )

    elif gpu_type == "apple_silicon":
        info = _get_apple_silicon_metrics()
        if info:
            return (
                info.memory_used_gb,
                info.memory_total_gb,
                info.memory_percent,
                info.name,
            )

    return (0.0, 0.0, 0.0, None)


def get_detailed_gpu_info() -> Optional[GPUInfo]:
    """Get detailed GPU information.

    Returns:
        GPUInfo object with full details, or None if no GPU
    """
    gpu_type = _detect_gpu_type()

    if gpu_type == "nvidia":
        return _get_nvidia_metrics()
    elif gpu_type == "apple_silicon":
        return _get_apple_silicon_metrics()

    return None


def is_gpu_available() -> bool:
    """Check if any supported GPU is available.

    Returns:
        True if NVIDIA or Apple Silicon GPU detected
    """
    return _detect_gpu_type() != "none"
