"""
Metadata package for WikiGen.
Centralized source of truth for project information.
"""

from .project import (
    PROJECT_NAME,
    AUTHOR_NAME,
    ORGANIZATION,
    DESCRIPTION,
    REPOSITORY_URL,
    HOMEPAGE_URL,
    ISSUES_URL,
    COPYRIGHT_TEXT,
    MIN_PYTHON_VERSION,
    CLI_ENTRY_POINT,
)

from .version import get_version, __version__

# Re-export commonly used items
__all__ = [
    "PROJECT_NAME",
    "AUTHOR_NAME",
    "ORGANIZATION",
    "DESCRIPTION",
    "REPOSITORY_URL",
    "HOMEPAGE_URL",
    "ISSUES_URL",
    "COPYRIGHT_TEXT",
    "MIN_PYTHON_VERSION",
    "CLI_ENTRY_POINT",
    "get_version",
    "__version__",
]
