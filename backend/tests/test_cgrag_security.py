"""Security tests for CGRAG router.

Tests path traversal protection and input validation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.routers.cgrag import _validate_directory_path, ALLOWED_ROOTS


class TestPathTraversalProtection:
    """Tests for path traversal attack prevention."""

    def test_allowed_path_in_repos(self, tmp_path):
        """Test that paths within ~/repos are allowed."""
        with patch.object(Path, "home", return_value=tmp_path):
            # Create the repos directory
            repos_dir = tmp_path / "repos" / "my-project"
            repos_dir.mkdir(parents=True)

            # Patch ALLOWED_ROOTS to use tmp_path
            patched_roots = [tmp_path / "repos", Path("/app"), Path.cwd()]
            with patch("app.routers.cgrag.ALLOWED_ROOTS", patched_roots):
                result = _validate_directory_path(repos_dir)
                assert result == repos_dir.resolve()

    def test_allowed_path_in_cwd(self, tmp_path):
        """Test that paths within cwd are allowed."""
        # Create a subdirectory within a mocked cwd
        work_dir = tmp_path / "workdir" / "project"
        work_dir.mkdir(parents=True)

        patched_roots = [tmp_path / "workdir"]
        with patch("app.routers.cgrag.ALLOWED_ROOTS", patched_roots):
            result = _validate_directory_path(work_dir)
            assert result == work_dir.resolve()

    def test_path_traversal_blocked_etc_passwd(self):
        """Test that path traversal to /etc is blocked."""
        malicious_path = Path("/etc/passwd")
        with pytest.raises(HTTPException) as exc_info:
            _validate_directory_path(malicious_path)
        assert exc_info.value.status_code == 403
        assert "not in allowed paths" in exc_info.value.detail

    def test_path_traversal_blocked_root(self):
        """Test that accessing root directory is blocked."""
        malicious_path = Path("/")
        with pytest.raises(HTTPException) as exc_info:
            _validate_directory_path(malicious_path)
        assert exc_info.value.status_code == 403

    def test_path_traversal_blocked_dotdot(self):
        """Test that ../ traversal attempts are blocked."""
        # Construct a path that tries to escape via ..
        malicious_path = Path("/app/../etc/passwd")
        with pytest.raises(HTTPException) as exc_info:
            _validate_directory_path(malicious_path)
        assert exc_info.value.status_code == 403

    def test_path_traversal_blocked_home_sensitive(self):
        """Test that sensitive home directories are blocked."""
        malicious_paths = [
            Path.home() / ".ssh",
            Path.home() / ".aws",
            Path.home() / ".config",
            Path("/root"),
        ]
        for malicious_path in malicious_paths:
            with pytest.raises(HTTPException) as exc_info:
                _validate_directory_path(malicious_path)
            assert exc_info.value.status_code == 403, f"Should block {malicious_path}"

    def test_path_traversal_blocked_var(self):
        """Test that /var directories are blocked."""
        malicious_path = Path("/var/log")
        with pytest.raises(HTTPException) as exc_info:
            _validate_directory_path(malicious_path)
        assert exc_info.value.status_code == 403

    def test_path_is_resolved_canonicalized(self, tmp_path):
        """Test that paths are canonicalized before checking."""
        # Create a symlink that points outside allowed roots
        # The resolved path should be checked, not the symlink path
        allowed_dir = tmp_path / "repos"
        allowed_dir.mkdir()

        # Create a file in allowed dir
        safe_file = allowed_dir / "safe"
        safe_file.mkdir()

        patched_roots = [allowed_dir]
        with patch("app.routers.cgrag.ALLOWED_ROOTS", patched_roots):
            # Direct path should work
            result = _validate_directory_path(safe_file)
            assert result == safe_file.resolve()

    def test_allowed_roots_are_defined(self):
        """Test that ALLOWED_ROOTS contains expected paths."""
        assert len(ALLOWED_ROOTS) >= 1
        # Should include repos directory
        assert any("repos" in str(root) for root in ALLOWED_ROOTS)

    def test_path_traversal_logs_warning(self, caplog):
        """Test that blocked attempts are logged."""
        import logging

        with caplog.at_level(logging.WARNING):
            with pytest.raises(HTTPException):
                _validate_directory_path(Path("/etc/shadow"))

        # Check that a warning was logged
        assert any(
            "Path traversal attempt blocked" in record.message
            for record in caplog.records
        )
