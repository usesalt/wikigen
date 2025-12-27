"""MCP server implementation for wikigen."""

from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .output_resources import discover_all_projects
from ..config import get_output_dir
from .search_index import FileIndexer

# Initialize the MCP server
# Instructions help editors/clients understand what this server provides
app = FastMCP(
    "wikigen",
    instructions=(
        "Expose local wiki markdown files as MCP tools. "
        "Available tools: search_docs (semantic search across indexed directories), "
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
    query: str,
    limit: int = 20,
    directory_filter: Optional[str] = None,
    chunk_limit: int = 5,
) -> str:
    """
    Search for markdown files across indexed directories using semantic search.

    This tool uses semantic search to find relevant chunks from indexed documentation.
    It returns relevant chunks with content snippets instead of entire files.
    Index directories first using index_directories, or files are auto-indexed from
    the configured output_dir on first search.

    Args:
        query: Search query (supports multi-word queries and natural language)
        limit: Maximum number of chunks to return (default: 20)
        directory_filter: Optional directory path to filter results
        chunk_limit: Maximum chunks per file (default: 5)

    Returns:
        Formatted list of relevant chunks with their paths, resource names, scores, and content snippets.
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

    # Always use semantic search
    if not indexer.enable_semantic_search or not indexer.vector_index:
        # Fallback to keyword search if semantic search is not available
        results = indexer.search(query, limit=limit, directory_filter=directory_filter)
        if not results:
            return f"No files found matching '{query}'."

        # Format file results
        lines = [f"Found {len(results)} file(s) matching '{query}':\n"]
        for i, result in enumerate(results, 1):
            lines.append(
                f"{i}. {result['resource_name']}\n"
                f"   Path: {result['file_path']}\n"
                f"   Directory: {result['directory']}"
            )
        return "\n".join(lines)

    # Use semantic search
    results = indexer.search_semantic(
        query,
        limit=limit,
        directory_filter=directory_filter,
        max_chunks_per_file=chunk_limit,
    )

    if not results:
        return f"No chunks found matching '{query}'."

    # Format chunk results
    lines = [f"Found {len(results)} relevant chunk(s) matching '{query}':\n"]
    for i, result in enumerate(results, 1):
        # Truncate chunk content for display (first 200 chars)
        content_snippet = result.get("content", "")[:200]
        if len(result.get("content", "")) > 200:
            content_snippet += "..."

        lines.append(
            f"{i}. {result['resource_name']} (chunk {result.get('chunk_index', 0)})\n"
            f"   Path: {result['file_path']}\n"
            f"   Score: {result.get('score', 0):.4f}\n"
            f"   Content: {content_snippet}"
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
