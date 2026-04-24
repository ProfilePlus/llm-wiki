"""MCP server implementation using stdio transport."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..context import WikiContext
from .tools import WikiTools

logger = logging.getLogger(__name__)


class WikiMCPServer:
    """MCP server for wiki operations."""

    def __init__(self, wiki_ctx: WikiContext):
        """
        Initialize MCP server.

        Args:
            wiki_ctx: Wiki context with config and paths
        """
        self.wiki_ctx = wiki_ctx
        self.server = Server("wiki-mcp")
        self.tools_instance = None

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="search_wiki",
                    description="Search wiki and get AI-generated answer based on wiki content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query or question"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_page",
                    description="Get wiki page content by slug",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "slug": {
                                "type": "string",
                                "description": "Page slug (filename without .md)"
                            }
                        },
                        "required": ["slug"]
                    }
                ),
                Tool(
                    name="get_backlinks",
                    description="Get pages that link to the specified page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "slug": {
                                "type": "string",
                                "description": "Target page slug"
                            }
                        },
                        "required": ["slug"]
                    }
                ),
                Tool(
                    name="get_thread",
                    description="Get thread details by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "thread_id": {
                                "type": "string",
                                "description": "Thread identifier"
                            }
                        },
                        "required": ["thread_id"]
                    }
                ),
                Tool(
                    name="get_recent_threads",
                    description="Get recent threads sorted by update time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of threads (default: 10)",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="get_decisions",
                    description="Get recent decisions from decision log",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of decisions (default: 20)",
                                "default": 20
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            if not self.tools_instance:
                return [TextContent(
                    type="text",
                    text="Error: Wiki tools not initialized"
                )]

            try:
                if name == "search_wiki":
                    result = self.tools_instance.search_wiki(arguments["query"])
                elif name == "get_page":
                    result = self.tools_instance.get_page(arguments["slug"])
                elif name == "get_backlinks":
                    result = self.tools_instance.get_backlinks(arguments["slug"])
                elif name == "get_thread":
                    result = self.tools_instance.get_thread(arguments["thread_id"])
                elif name == "get_recent_threads":
                    limit = arguments.get("limit", 10)
                    result = self.tools_instance.get_recent_threads(limit)
                elif name == "get_decisions":
                    limit = arguments.get("limit", 20)
                    result = self.tools_instance.get_decisions(limit)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                import json
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
            except Exception as e:
                logger.error(f"Tool call error: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

    async def run(self):
        """Run the MCP server."""
        # Initialize tools
        if not self.wiki_ctx.wiki_path or not self.wiki_ctx.wiki_path.exists():
            raise ValueError("Wiki path not configured or does not exist")

        try:
            provider = self.wiki_ctx.create_provider()
        except Exception as e:
            raise ValueError(f"Failed to create provider: {e}")

        self.tools_instance = WikiTools(
            wiki_path=self.wiki_ctx.wiki_path,
            provider=provider,
            language=self.wiki_ctx.language
        )

        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def run_server(wiki_ctx: WikiContext):
    """Run MCP server (sync wrapper)."""
    server = WikiMCPServer(wiki_ctx)
    asyncio.run(server.run())
