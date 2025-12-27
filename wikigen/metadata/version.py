"""
Version management for WikiGen.
Centralized version definition for consistency.
"""

# Current version - update this when releasing
__version__ = "1.0.0"


def get_version():
    """
    Get the current version.

    Returns:
        str: The current version string (e.g., "1.0.0")
    """
    return __version__
