"""Output directory resource mapping for MCP server.

This module provides resource name mapping for files in the configured output directory.
Resource names are derived from file paths relative to the output directory.
"""

from pathlib import Path
from typing import Dict

from ..config import get_output_dir


def discover_projects(output_dir: Path) -> Dict[str, Path]:
    """
    Discover all markdown documentation files in the output directory.

    Searches recursively for all .md files using efficient glob pattern:
    - Direct files: output/file.md -> key: "file"
    - Nested files: output/folder/file.md -> key: "folder/file"
    - Uses rglob for recursive search (more efficient than manual iteration)

    Args:
        output_dir: Base directory where documentation is stored

    Returns:
        Dictionary mapping resource names to their documentation file paths
    """
    projects = {}

    if not output_dir.exists():
        return projects

    # Use rglob to efficiently find all .md files recursively
    # rglob is optimized and much faster for directory iteration
    for md_file in output_dir.rglob("*.md"):
        # Get relative path from output_dir to maintain folder structure in resource name
        try:
            relative_path = md_file.relative_to(output_dir)
            # Remove .md extension and use path components as resource name
            # Example: "folder/file.md" -> "folder/file"
            # Example: "file.md" -> "file"
            resource_name = str(relative_path.with_suffix(""))

            # Skip hidden files/directories (e.g., .git, .cursor)
            # Only skip if any parent directory is hidden, not the file itself
            if any(part.startswith(".") for part in relative_path.parts[:-1]):
                continue

            projects[resource_name] = md_file
        except ValueError:
            # File is not relative to output_dir (shouldn't happen, but safety check)
            continue

    return projects


def discover_all_projects() -> Dict[str, Path]:
    """
    Discover all markdown files using configured output directory.

    Returns:
        Dictionary mapping resource names to their documentation file paths
    """
    output_dir = get_output_dir()
    return discover_projects(output_dir)
