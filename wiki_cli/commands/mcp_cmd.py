"""wiki mcp - MCP server commands."""

import click
import json
import sys
from pathlib import Path
from rich.console import Console

from ..context import WikiContext
from ..mcp.server import run_server
from ..mcp.daemon import WikiDaemon

console = Console()


@click.group()
def mcp():
    """MCP server commands."""
    pass


@mcp.command()
@click.pass_context
def serve(ctx):
    """Start MCP server in foreground (stdio mode)."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]Error: No active domain. Run: wiki domain use <name>[/red]")
        sys.exit(1)

    if not wiki_ctx.active_provider:
        console.print("[red]Error: No active provider. Run: wiki provider use <name>[/red]")
        sys.exit(1)

    if not wiki_ctx.wiki_path or not wiki_ctx.wiki_path.exists():
        console.print("[red]Error: Wiki directory does not exist[/red]")
        sys.exit(1)

    try:
        run_server(wiki_ctx)
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        sys.exit(1)


@mcp.command()
@click.pass_context
def start(ctx):
    """Start MCP server in daemon mode."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]Error: No active domain[/red]")
        sys.exit(1)

    if not wiki_ctx.active_provider:
        console.print("[red]Error: No active provider[/red]")
        sys.exit(1)

    # Setup daemon files
    daemon_dir = wiki_ctx.data_dir / ".daemon"
    daemon_dir.mkdir(exist_ok=True)
    pid_file = daemon_dir / "mcp.pid"
    log_file = daemon_dir / "mcp.log"

    daemon = WikiDaemon(pid_file, log_file)

    if daemon.is_running():
        console.print(f"[yellow]MCP server already running (PID: {daemon.get_pid()})[/yellow]")
        return

    try:
        pid = daemon.start(run_server, wiki_ctx)
        console.print(f"[green]✓[/green] MCP server started (PID: {pid})")
        console.print(f"  Log: {log_file}")
    except Exception as e:
        console.print(f"[red]Failed to start daemon: {e}[/red]")
        sys.exit(1)


@mcp.command()
@click.pass_context
def stop(ctx):
    """Stop MCP daemon server."""
    wiki_ctx: WikiContext = ctx.obj

    daemon_dir = wiki_ctx.data_dir / ".daemon"
    pid_file = daemon_dir / "mcp.pid"
    log_file = daemon_dir / "mcp.log"

    daemon = WikiDaemon(pid_file, log_file)

    if not daemon.is_running():
        console.print("[yellow]MCP server not running[/yellow]")
        return

    try:
        daemon.stop()
        console.print("[green]✓[/green] MCP server stopped")
    except Exception as e:
        console.print(f"[red]Failed to stop daemon: {e}[/red]")
        sys.exit(1)


@mcp.command()
@click.pass_context
def status(ctx):
    """Check MCP server status."""
    wiki_ctx: WikiContext = ctx.obj

    daemon_dir = wiki_ctx.data_dir / ".daemon"
    pid_file = daemon_dir / "mcp.pid"
    log_file = daemon_dir / "mcp.log"

    daemon = WikiDaemon(pid_file, log_file)

    if daemon.is_running():
        console.print(f"[green]MCP server running[/green] (PID: {daemon.get_pid()})")
    else:
        console.print("[dim]MCP server not running[/dim]")


@mcp.command()
@click.option("--tool", type=click.Choice(["cc", "codex", "gemini", "all"]), default="all")
@click.pass_context
def setup(ctx, tool):
    """Generate MCP configuration for AI tools."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]Error: No active domain[/red]")
        sys.exit(1)

    # Get wiki CLI path
    import shutil
    wiki_bin = shutil.which("wiki")
    if not wiki_bin:
        console.print("[red]Error: wiki command not found in PATH[/red]")
        sys.exit(1)

    configs = {}

    # Claude Code (CC) config
    if tool in ["cc", "all"]:
        cc_config = {
            "mcpServers": {
                "wiki": {
                    "command": wiki_bin,
                    "args": ["mcp", "serve"],
                    "env": {
                        "WIKI_DOMAIN": wiki_ctx.active_domain
                    }
                }
            }
        }
        configs["claude_code"] = cc_config

    # CodeX config (similar format)
    if tool in ["codex", "all"]:
        codex_config = {
            "mcpServers": {
                "wiki": {
                    "command": wiki_bin,
                    "args": ["mcp", "serve"]
                }
            }
        }
        configs["codex"] = codex_config

    # Gemini config
    if tool in ["gemini", "all"]:
        gemini_config = {
            "servers": {
                "wiki": {
                    "command": wiki_bin,
                    "args": ["mcp", "serve"]
                }
            }
        }
        configs["gemini"] = gemini_config

    # Display configs
    console.print("[cyan]MCP Configuration:[/cyan]\n")

    if "claude_code" in configs:
        console.print("[bold]Claude Code (~/.claude/settings.json):[/bold]")
        console.print(json.dumps(configs["claude_code"], indent=2))
        console.print()

    if "codex" in configs:
        console.print("[bold]CodeX (~/.codex/config.json):[/bold]")
        console.print(json.dumps(configs["codex"], indent=2))
        console.print()

    if "gemini" in configs:
        console.print("[bold]Gemini (~/.gemini/mcp.json):[/bold]")
        console.print(json.dumps(configs["gemini"], indent=2))
        console.print()

    console.print("[dim]Copy the relevant config to your AI tool's configuration file.[/dim]")
