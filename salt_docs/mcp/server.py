"""MCP server implementation for salt-docs."""

from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .output_resources import discover_all_projects
from ..config import get_output_dir
from .search_index import FileIndexer

# Initialize the MCP server
# Instructions help editors/clients understand what this server provides
app = FastMCP(
    "salt-docs",
    instructions=(
        "Expose local wiki markdown files as MCP tools. "
        "Available tools: list_docs (list output_dir docs), search_docs (fast machine-wide search), "
        "get_docs (fetch content by resource name or file path), and index_directories (index dirs for search). "
        "Doc names mirror paths under your configured output_dir (without .md extension)."
    ),
)

# Initialize search indexer for fast machine-wide search
_indexer: Optional[FileIndexer] = None


def _get_indexer() -> FileIndexer:
    """Get or create the search indexer instance."""
    global _indexer
    if _indexer is None:
        _indexer = FileIndexer()
    return _indexer


# Store discovered projects (refreshed on each request)
_projects: Dict[str, Path] = {}


def _refresh_projects():
    """Refresh the project registry."""
    global _projects
    _projects = discover_all_projects()


def _get_project_resources():
    """Get list of available project resources."""
    _refresh_projects()
    return _projects


# MCP Tools - executable actions for interacting with documentation
@app.tool()
def list_docs() -> str:
    """List all available documentation files with their IDs/names."""
    projects = _get_project_resources()
    if not projects:
        return "No documentation files found in the output directory."

    doc_list = "\n".join(f"- {name}" for name in sorted(projects.keys()))
    return f"Available documentation files ({len(projects)} total):\n\n{doc_list}"


@app.tool()
def get_docs(identifier: str) -> str:
    """
    Get the full content of a documentation file by resource name or absolute file path.

    This tool can fetch documentation using either:
    - Resource name (e.g., 'README', 'Order Management/Felis Stream') - searches output_dir
    - Absolute file path (e.g., '/Users/name/Documents/doc.md') - works with any indexed file

    Args:
        identifier: Either a resource name (from output_dir) or an absolute file path

    Returns:
        The markdown content of the requested documentation file.
    """
    # Check if it looks like an absolute path
    path_obj = Path(identifier)
    if path_obj.is_absolute() and path_obj.exists():
        # Treat as absolute file path
        try:
            content = path_obj.read_text(encoding="utf-8")
            return content
        except Exception as e:
            raise RuntimeError(
                f"Failed to read file at path '{identifier}': {e}"
            ) from e

    # Treat as resource name from output_dir
    projects = _get_project_resources()

    if identifier not in projects:
        # Provide helpful error message
        available = ", ".join(sorted(projects.keys())[:10]) if projects else "none"
        if len(projects) > 10:
            available += f" ... (and {len(projects) - 10} more)"
        raise ValueError(
            f"Documentation '{identifier}' not found in output directory. "
            f"Available resources: {available}. "
            f"If you meant to use a file path, provide an absolute path starting with '/'."
        )

    doc_path = projects[identifier]
    try:
        content = doc_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        raise RuntimeError(
            f"Failed to read documentation for '{identifier}': {e}"
        ) from e


@app.tool()
def search_docs(
    query: str, limit: int = 20, directory_filter: Optional[str] = None
) -> str:
    """
    Search for markdown files across indexed directories using fast full-text search.

    This tool searches file paths, names, and resource names. Index directories first
    using the indexer, or files are auto-indexed from the configured output_dir.

    Args:
        query: Search query (supports multi-word queries)
        limit: Maximum number of results (default: 20)
        directory_filter: Optional directory path to filter results

    Returns:
        Formatted list of matching files with their paths and resource names.
    """
    indexer = _get_indexer()

    # Auto-index default output directory if no files indexed yet
    stats = indexer.get_stats()
    if stats["total_files"] == 0:
        output_dir = get_output_dir()
        if output_dir.exists():
            added, updated, skipped = indexer.index_directory(output_dir)
            if added > 0 or updated > 0:
                return f"Indexed {added} new files, updated {updated}. Try searching again."

    results = indexer.search(query, limit=limit, directory_filter=directory_filter)

    if not results:
        return f"No files found matching '{query}'."

    # Format results
    lines = [f"Found {len(results)} file(s) matching '{query}':\n"]
    for i, result in enumerate(results, 1):
        lines.append(
            f"{i}. {result['resource_name']}\n"
            f"   Path: {result['file_path']}\n"
            f"   Directory: {result['directory']}"
        )

    return "\n".join(lines)


@app.tool()
def index_directories(directories: List[str], max_depth: Optional[int] = None) -> str:
    """
    Index markdown files from specified directories for fast searching.

    Args:
        directories: List of directory paths to index
        max_depth: Maximum recursion depth (None = unlimited)

    Returns:
        Summary of indexing results.
    """
    indexer = _get_indexer()

    total_added = 0
    total_updated = 0
    total_skipped = 0

    results = []

    for dir_path in directories:
        path = Path(dir_path).expanduser()
        if not path.exists():
            results.append(f"✗ {dir_path}: Directory does not exist")
            continue

        if not path.is_dir():
            results.append(f"✗ {dir_path}: Path is not a directory")
            continue

        added, updated, skipped = indexer.index_directory(path, max_depth=max_depth)
        total_added += added
        total_updated += updated
        total_skipped += skipped

        results.append(
            f"✓ {dir_path}: {added} added, {updated} updated, {skipped} skipped"
        )

    summary = "\n".join(results)
    summary += f"\n\nTotal: {total_added} added, {total_updated} updated, {total_skipped} skipped"

    return summary


def run_mcp_server():
    """Entry point to run MCP server."""
    app.run()
