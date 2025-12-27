"""
Tests for version checking functionality.
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from wikigen.utils.version_check import (
    fetch_latest_version,
    compare_versions,
    check_for_update,
)
from wikigen.config import (
    should_check_for_updates,
    update_last_check_timestamp,
    load_config,
    save_config,
)


class TestVersionComparison:
    """Test version comparison logic."""

    def test_compare_versions_newer_patch(self):
        """Test comparing versions with newer patch version."""
        assert compare_versions("0.1.5", "0.1.6") is True
        assert compare_versions("0.1.5", "0.1.5") is False
        assert compare_versions("0.1.6", "0.1.5") is False

    def test_compare_versions_newer_minor(self):
        """Test comparing versions with newer minor version."""
        assert compare_versions("0.1.5", "0.2.0") is True
        assert compare_versions("0.2.0", "0.1.5") is False

    def test_compare_versions_newer_major(self):
        """Test comparing versions with newer major version."""
        assert compare_versions("0.1.5", "1.0.0") is True
        assert compare_versions("1.0.0", "0.1.5") is False

    def test_compare_versions_different_length(self):
        """Test comparing versions with different number of parts."""
        assert compare_versions("0.1", "0.1.5") is True
        assert compare_versions("0.1.5", "0.1") is False
        assert compare_versions("0.1.0", "0.2") is True

    def test_compare_versions_fallback_to_string(self):
        """Test that invalid version formats fall back to string comparison."""
        # Non-numeric versions should use string comparison
        assert compare_versions("0.1.5a", "0.1.5b") is True  # "b" > "a"
        assert compare_versions("dev", "0.1.0") is False  # String comparison


class TestFetchLatestVersion:
    """Test fetching latest version from PyPI."""

    @patch("wikigen.utils.version_check.requests.get")
    def test_fetch_latest_version_success(self, mock_get):
        """Test successful version fetch from PyPI."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"info": {"version": "0.1.6"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        version = fetch_latest_version()
        assert version == "0.1.6"
        mock_get.assert_called_once_with(
            "https://pypi.org/pypi/wikigen/json", timeout=5.0
        )

    @patch("wikigen.utils.version_check.requests.get")
    def test_fetch_latest_version_network_error(self, mock_get):
        """Test that network errors return None."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        version = fetch_latest_version()
        assert version is None

    @patch("wikigen.utils.version_check.requests.get")
    def test_fetch_latest_version_invalid_response(self, mock_get):
        """Test that invalid JSON responses return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        version = fetch_latest_version()
        assert version is None

    @patch("wikigen.utils.version_check.requests.get")
    def test_fetch_latest_version_custom_package(self, mock_get):
        """Test fetching version with custom package name."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"info": {"version": "1.0.0"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        version = fetch_latest_version(package_name="custom-package")
        assert version == "1.0.0"
        mock_get.assert_called_once_with(
            "https://pypi.org/pypi/custom-package/json", timeout=5.0
        )


class TestCheckForUpdate:
    """Test the check_for_update function."""

    @patch("wikigen.utils.version_check.fetch_latest_version")
    def test_check_for_update_available(self, mock_fetch):
        """Test when an update is available."""
        mock_fetch.return_value = "0.1.6"

        result = check_for_update("0.1.5")
        assert result == "0.1.6"

    @patch("wikigen.utils.version_check.fetch_latest_version")
    def test_check_for_update_not_available(self, mock_fetch):
        """Test when no update is available (same version)."""
        mock_fetch.return_value = "0.1.5"

        result = check_for_update("0.1.5")
        assert result is None

    @patch("wikigen.utils.version_check.fetch_latest_version")
    def test_check_for_update_current_newer(self, mock_fetch):
        """Test when current version is newer (shouldn't happen but test anyway)."""
        mock_fetch.return_value = "0.1.5"

        result = check_for_update("0.1.6")
        assert result is None

    @patch("wikigen.utils.version_check.fetch_latest_version")
    def test_check_for_update_network_error(self, mock_fetch):
        """Test when network error occurs."""
        mock_fetch.return_value = None

        result = check_for_update("0.1.5")
        assert result is None


class TestConfigHelpers:
    """Test configuration helper functions for update checks."""

    def test_should_check_for_updates_never_checked(self):
        """Test that we should check if never checked before."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with patch("wikigen.config.CONFIG_FILE", config_path):
                # Create config without last_update_check
                config = {"output_dir": "/tmp"}
                save_config(config)

                assert should_check_for_updates() is True

    def test_should_check_for_updates_just_checked(self):
        """Test that we shouldn't check if just checked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with patch("wikigen.config.CONFIG_FILE", config_path):
                # Set last check to now
                config = {"output_dir": "/tmp", "last_update_check": time.time()}
                save_config(config)

                assert should_check_for_updates() is False

    def test_should_check_for_updates_24h_passed(self):
        """Test that we should check if 24+ hours have passed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with patch("wikigen.config.CONFIG_FILE", config_path):
                # Set last check to 25 hours ago
                config = {
                    "output_dir": "/tmp",
                    "last_update_check": time.time() - (25 * 3600),
                }
                save_config(config)

                assert should_check_for_updates() is True

    def test_update_last_check_timestamp(self):
        """Test updating the last check timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            with patch("wikigen.config.CONFIG_FILE", config_path):
                # Initially no timestamp
                config = {"output_dir": "/tmp"}
                save_config(config)

                # Update timestamp
                update_last_check_timestamp()

                # Check it was saved
                updated_config = load_config()
                assert "last_update_check" in updated_config
                assert updated_config["last_update_check"] is not None
                assert isinstance(updated_config["last_update_check"], float)
                # Should be recent (within last minute)
                assert time.time() - updated_config["last_update_check"] < 60


class TestCLIIntegration:
    """Test CLI integration of version checking."""

    @patch("wikigen.cli.should_check_for_updates")
    @patch("wikigen.cli.check_for_update")
    @patch("wikigen.cli.update_last_check_timestamp")
    @patch("wikigen.cli.print_update_notification")
    def test_check_updates_called_on_success(
        self, mock_notify, mock_update_ts, mock_check, mock_should
    ):
        """Test that update check is called after successful execution."""
        from wikigen.cli import _check_for_updates_quietly

        mock_should.return_value = True
        mock_check.return_value = "0.1.6"

        with patch("wikigen.cli.get_version", return_value="0.1.5"):
            _check_for_updates_quietly()

        mock_should.assert_called_once()
        mock_check.assert_called_once()
        mock_update_ts.assert_called_once()
        mock_notify.assert_called_once_with("0.1.5", "0.1.6")

    @patch("wikigen.cli.should_check_for_updates")
    @patch("wikigen.cli.check_for_update")
    @patch("wikigen.cli.update_last_check_timestamp")
    @patch("wikigen.cli.print_update_notification")
    def test_check_updates_skipped_if_too_recent(
        self, mock_notify, mock_update_ts, mock_check, mock_should
    ):
        """Test that update check is skipped if checked recently."""
        from wikigen.cli import _check_for_updates_quietly

        mock_should.return_value = False

        _check_for_updates_quietly()

        mock_should.assert_called_once()
        mock_check.assert_not_called()
        mock_update_ts.assert_not_called()
        mock_notify.assert_not_called()

    @patch("wikigen.cli.should_check_for_updates")
    @patch("wikigen.cli.check_for_update")
    @patch("wikigen.cli.update_last_check_timestamp")
    @patch("wikigen.cli.print_update_notification")
    def test_check_updates_no_notification_if_no_update(
        self, mock_notify, mock_update_ts, mock_check, mock_should
    ):
        """Test that no notification is shown if no update available."""
        from wikigen.cli import _check_for_updates_quietly

        mock_should.return_value = True
        mock_check.return_value = None  # No update available

        with patch("wikigen.cli.get_version", return_value="0.1.5"):
            _check_for_updates_quietly()

        mock_check.assert_called_once()
        mock_update_ts.assert_called_once()
        mock_notify.assert_not_called()

    @patch("wikigen.cli.should_check_for_updates")
    @patch("wikigen.cli.check_for_update")
    @patch("wikigen.cli.update_last_check_timestamp")
    @patch("wikigen.cli.print_update_notification")
    def test_check_updates_handles_exceptions_gracefully(
        self, mock_notify, mock_update_ts, mock_check, mock_should
    ):
        """Test that exceptions are handled gracefully."""
        from wikigen.cli import _check_for_updates_quietly

        mock_should.return_value = True
        mock_check.side_effect = Exception("Unexpected error")

        # Should not raise
        _check_for_updates_quietly()

        mock_update_ts.assert_not_called()
        mock_notify.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
