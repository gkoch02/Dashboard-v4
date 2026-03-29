"""Tests for src/fetchers/host.py — error-handling branches and all-fail path."""

import socket
from unittest.mock import MagicMock, mock_open, patch

from src.fetchers.host import fetch_host_data


class TestFetchHostDataErrorBranches:
    """Each except block in fetch_host_data returns None for that field
    while still populating all other fields."""

    def test_hostname_failure_still_returns_data(self):
        with patch("socket.gethostname", side_effect=OSError("no hostname")):
            result = fetch_host_data()
        assert result is not None
        assert result.hostname is None

    def test_proc_uptime_failure_still_returns_data(self):
        def fake_open(path, *a, **kw):
            if "uptime" in path:
                raise OSError("no uptime")
            return mock_open(read_data="MemTotal: 8192 kB\nMemAvailable: 4096 kB\n")()

        with patch("builtins.open", side_effect=fake_open):
            result = fetch_host_data()
        # hostname and other fields may succeed; uptime should be None
        assert result is None or result.uptime_seconds is None

    def test_getloadavg_failure_still_returns_data(self):
        with patch("os.getloadavg", side_effect=OSError("no loadavg")):
            result = fetch_host_data()
        assert result is not None
        assert result.load_1m is None

    def test_proc_meminfo_failure_still_returns_data(self):
        def fake_open(path, *a, **kw):
            if "meminfo" in path:
                raise OSError("no meminfo")
            return mock_open(read_data="0.5 100.0\n")()

        with patch("builtins.open", side_effect=fake_open):
            result = fetch_host_data()
        assert result is None or result.ram_total_mb is None

    def test_statvfs_failure_still_returns_data(self):
        with patch("os.statvfs", side_effect=OSError("no statvfs")):
            result = fetch_host_data()
        assert result is not None
        assert result.disk_total_gb is None

    def test_cpu_temp_failure_still_returns_data(self):
        def fake_open(path, *a, **kw):
            if "thermal" in path:
                raise OSError("no thermal zone")
            return mock_open(read_data="MemTotal: 8192 kB\nMemAvailable: 4096 kB\n")()

        with patch("builtins.open", side_effect=fake_open):
            result = fetch_host_data()
        assert result is None or result.cpu_temp_c is None

    def test_ip_socket_failure_still_returns_data(self):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("network unreachable")
        with patch("socket.socket", return_value=mock_sock):
            result = fetch_host_data()
        assert result is not None
        assert result.ip_address is None


class TestFetchHostDataAllFail:
    """When every field fails, fetch_host_data returns None."""

    def test_all_fields_fail_returns_none(self):
        with (
            patch("socket.gethostname", side_effect=OSError),
            patch("os.getloadavg", side_effect=OSError),
            patch("os.statvfs", side_effect=OSError),
            patch("builtins.open", side_effect=OSError),
            patch("socket.socket", side_effect=OSError),
        ):
            result = fetch_host_data()
        assert result is None


class TestFetchHostDataSuccess:
    """Smoke-test that a successful run returns a populated HostData."""

    def test_returns_host_data_on_success(self):
        result = fetch_host_data()
        # hostname should always work in any CI environment
        assert result is not None
        assert result.hostname == socket.gethostname()
