"""Tests for GPU monitoring utilities."""

import platform
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from app.services.gpu_monitor import (
    GPUInfo,
    _detect_gpu_type,
    _get_nvidia_metrics,
    _get_apple_silicon_metrics,
    get_gpu_metrics,
    get_detailed_gpu_info,
    is_gpu_available,
)


class TestGPUDetection:
    """Tests for GPU type detection."""

    def setup_method(self):
        """Reset cached GPU type before each test."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = None

    def test_detect_nvidia_gpu(self):
        """Test NVIDIA GPU detection via nvidia-smi."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="NVIDIA GeForce RTX 4090\n"
            )
            
            result = _detect_gpu_type()
            
            assert result == "nvidia"
            mock_run.assert_called()

    def test_detect_apple_silicon_via_cpu_brand(self):
        """Test Apple Silicon detection via CPU brand string."""
        with patch("subprocess.run") as mock_run, \
             patch("platform.system", return_value="Darwin"):
            
            # First call (nvidia-smi) fails
            # Second call (sysctl) returns Apple chip
            mock_run.side_effect = [
                FileNotFoundError(),  # nvidia-smi
                MagicMock(returncode=0, stdout="Apple M4 Pro\n"),  # sysctl
            ]
            
            result = _detect_gpu_type()
            
            assert result == "apple_silicon"

    def test_detect_apple_silicon_via_arm64(self):
        """Test Apple Silicon detection via arm64 architecture."""
        with patch("subprocess.run") as mock_run, \
             patch("platform.system", return_value="Darwin"):
            
            mock_run.side_effect = [
                FileNotFoundError(),  # nvidia-smi
                MagicMock(returncode=1, stdout=""),  # sysctl fails
                MagicMock(returncode=0, stdout="arm64\n"),  # uname -m
            ]
            
            result = _detect_gpu_type()
            
            assert result == "apple_silicon"

    def test_detect_no_gpu(self):
        """Test fallback when no GPU is detected."""
        with patch("subprocess.run") as mock_run, \
             patch("platform.system", return_value="Linux"):
            
            mock_run.side_effect = FileNotFoundError()
            
            result = _detect_gpu_type()
            
            assert result == "none"

    def test_gpu_type_caching(self):
        """Test that GPU type detection is cached."""
        import app.services.gpu_monitor as gpu_mod
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="NVIDIA GeForce RTX 4090\n"
            )
            
            # First call
            result1 = _detect_gpu_type()
            call_count_1 = mock_run.call_count
            
            # Second call should use cache
            result2 = _detect_gpu_type()
            call_count_2 = mock_run.call_count
            
            assert result1 == result2 == "nvidia"
            assert call_count_1 == call_count_2  # No additional calls


class TestNvidiaMetrics:
    """Tests for NVIDIA GPU metrics collection."""

    def test_get_nvidia_metrics_success(self):
        """Test successful NVIDIA metrics parsing."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="NVIDIA GeForce RTX 4090, 8192, 24576, 45\n"
            )
            
            result = _get_nvidia_metrics()
            
            assert result is not None
            assert result.name == "NVIDIA GeForce RTX 4090"
            assert result.memory_used_gb == pytest.approx(8.0, rel=0.01)
            assert result.memory_total_gb == pytest.approx(24.0, rel=0.01)
            assert result.memory_percent == pytest.approx(33.33, rel=0.1)
            assert result.gpu_utilization == 45.0
            assert result.is_unified_memory is False

    def test_get_nvidia_metrics_multi_gpu(self):
        """Test that first GPU is used for multi-GPU systems."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="NVIDIA GeForce RTX 4090, 8192, 24576, 45\nNVIDIA GeForce RTX 3080, 4096, 10240, 30\n"
            )
            
            result = _get_nvidia_metrics()
            
            assert result is not None
            assert result.name == "NVIDIA GeForce RTX 4090"

    def test_get_nvidia_metrics_failure(self):
        """Test graceful handling of nvidia-smi failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = _get_nvidia_metrics()
            
            assert result is None

    def test_get_nvidia_metrics_timeout(self):
        """Test graceful handling of nvidia-smi timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5)
            
            result = _get_nvidia_metrics()
            
            assert result is None


class TestAppleSiliconMetrics:
    """Tests for Apple Silicon metrics collection."""

    def test_get_apple_silicon_metrics_success(self):
        """Test successful Apple Silicon metrics collection."""
        mock_memory = MagicMock()
        mock_memory.used = 16 * 1024 ** 3  # 16 GB
        mock_memory.total = 24 * 1024 ** 3  # 24 GB
        mock_memory.percent = 66.7
        
        with patch("app.services.gpu_monitor.psutil") as mock_psutil, \
             patch("subprocess.run") as mock_run:
            mock_psutil.virtual_memory.return_value = mock_memory
            
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Apple M4 Pro\n"
            )
            
            result = _get_apple_silicon_metrics()
            
            assert result is not None
            assert "M4 Pro" in result.name
            assert "Unified Memory" in result.name
            assert result.memory_used_gb == pytest.approx(16.0, rel=0.01)
            assert result.memory_total_gb == pytest.approx(24.0, rel=0.01)
            assert result.is_unified_memory is True
            assert result.gpu_utilization is None


class TestGetGPUMetrics:
    """Tests for the main get_gpu_metrics function."""

    def setup_method(self):
        """Reset cached GPU type before each test."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = None

    def test_get_gpu_metrics_nvidia(self):
        """Test get_gpu_metrics with NVIDIA GPU."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = "nvidia"
        
        with patch.object(gpu_mod, "_get_nvidia_metrics") as mock_nvidia:
            mock_nvidia.return_value = GPUInfo(
                name="RTX 4090",
                memory_used_gb=8.0,
                memory_total_gb=24.0,
                memory_percent=33.33
            )
            
            used, total, percent, name = get_gpu_metrics()
            
            assert used == 8.0
            assert total == 24.0
            assert percent == pytest.approx(33.33)
            assert name == "RTX 4090"

    def test_get_gpu_metrics_no_gpu(self):
        """Test get_gpu_metrics with no GPU."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = "none"
        
        used, total, percent, name = get_gpu_metrics()
        
        assert used == 0.0
        assert total == 0.0
        assert percent == 0.0
        assert name is None


class TestIsGPUAvailable:
    """Tests for is_gpu_available function."""

    def setup_method(self):
        """Reset cached GPU type before each test."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = None

    def test_gpu_available_nvidia(self):
        """Test GPU available with NVIDIA."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = "nvidia"
        
        assert is_gpu_available() is True

    def test_gpu_available_apple_silicon(self):
        """Test GPU available with Apple Silicon."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = "apple_silicon"
        
        assert is_gpu_available() is True

    def test_gpu_not_available(self):
        """Test GPU not available."""
        import app.services.gpu_monitor as gpu_mod
        gpu_mod._cached_gpu_type = "none"
        
        assert is_gpu_available() is False
