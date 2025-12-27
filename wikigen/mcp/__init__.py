"""MCP (Model Context Protocol) server for wikigen."""


# Lazy import to avoid requiring mcp package at module load time
def run_mcp_server():
    """Entry point to run MCP server."""
    from .server import run_mcp_server as _run

    _run()  # run_mcp_server() doesn't return, it runs the server


__all__ = ["run_mcp_server"]
