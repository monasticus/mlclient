"""MCP server package exposing MarkLogic operations through mlclient.

The server is optional and requires the ``mcp`` extra::

    pip install mlclient[mcp]

Run it over stdio with ``python -m mlclient.mcp``. It exports the following:

    * mcp
        The configured FastMCP server instance.
    * main
        An entry point running the server over stdio transport.
"""

from mlclient.mcp.server import main, mcp

__all__ = ["main", "mcp"]
