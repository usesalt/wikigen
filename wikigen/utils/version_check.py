"""
Version checking utilities for WikiGen CLI.
Queries PyPI API to check for available updates.
"""

import requests
from typing import Optional


def fetch_latest_version(
    package_name: str = "wikigen", timeout: float = 5.0
) -> Optional[str]:
    """
    Fetch the latest version from PyPI API.

    Args:
        package_name: Name of the package on PyPI
        timeout: Request timeout in seconds

    Returns:
        Latest version string if successful, None otherwise
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        return data.get("info", {}).get("version")
    except (requests.RequestException, KeyError, ValueError, Exception):
        # Silently fail - don't interrupt user workflow
        # Catch all exceptions to ensure CLI never breaks due to update check
        return None


def compare_versions(current_version: str, latest_version: str) -> bool:
    """
    Compare two version strings to determine if latest is newer.

    Uses simple semantic version comparison (e.g., "0.1.5" vs "0.1.6").

    Args:
        current_version: Currently installed version
        latest_version: Latest available version from PyPI

    Returns:
        True if latest_version is newer than current_version
    """
    try:
        # Simple tuple comparison works for semantic versions
        current_parts = tuple(map(int, current_version.split(".")))
        latest_parts = tuple(map(int, latest_version.split(".")))

        # Pad shorter version with zeros for comparison
        max_len = max(len(current_parts), len(latest_parts))
        current_parts = current_parts + (0,) * (max_len - len(current_parts))
        latest_parts = latest_parts + (0,) * (max_len - len(latest_parts))

        return latest_parts > current_parts
    except (ValueError, AttributeError):
        # If version format is unexpected, fall back to string comparison
        return latest_version > current_version


def check_for_update(current_version: str, timeout: float = 5.0) -> Optional[str]:
    """
    Check if a newer version is available on PyPI.

    Args:
        current_version: Currently installed version
        timeout: Request timeout in seconds

    Returns:
        Latest version string if update is available, None otherwise
    """
    latest_version = fetch_latest_version(timeout=timeout)

    if not latest_version:
        return None

    if compare_versions(current_version, latest_version):
        return latest_version

    return None
