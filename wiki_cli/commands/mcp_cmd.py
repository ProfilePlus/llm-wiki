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
@click.option("--test", is_flag=True, help="Test mode (print info and exit)")
@click.pass_context
def serve(ctx, test):
    """Start MCP server in foreground (stdio mode).

    ⚠️  This command is designed to be called by AI tools (Claude Code, CodeX, Gemini),
    not run directly in terminal. Use 'wiki mcp start' for daemon mode instead.
    """
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

    if test:
        console.print("[green]✓[/green] MCP server configuration OK")
        console.print(f"  Domain: {wiki_ctx.active_domain}")
        console.print(f"  Provider: {wiki_ctx.active_provider}")
        console.print(f"  Wiki path: {wiki_ctx.wiki_path}")
        console.print("\n[dim]To start daemon: wiki mcp start[/dim]")
        return

    # Check if running in terminal (not as subprocess)
    if sys.stdin.isatty():
        console.print("[yellow]⚠️  Warning: MCP server should not be run directly in terminal.[/yellow]")
        console.print("\nThis command is designed to be called by AI tools via stdio.")
        console.print("\n[bold]To use MCP server:[/bold]")
        console.print("  1. Start daemon:  [cyan]wiki mcp start[/cyan]")
        console.print("  2. Configure AI:  [cyan]wiki mcp setup[/cyan]")
        console.print("  3. Test config:   [cyan]wiki mcp serve --test[/cyan]")
        console.print("\n[dim]Press Ctrl+C to exit, or wait for AI tool to connect...[/dim]\n")

    try:
        run_server(wiki_ctx)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
        sys.exit(0)
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
@click.pass_context
def setup(ctx):
    """Interactive MCP configuration for AI tools."""
    import shutil
    from rich.prompt import Confirm

    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]Error: No active domain[/red]")
        sys.exit(1)

    wiki_bin = shutil.which("wiki")
    if not wiki_bin:
        console.print("[red]Error: wiki command not found in PATH[/red]")
        sys.exit(1)

    mcp_entry = {
        "command": wiki_bin,
        "args": ["mcp", "serve"],
        "env": {"WIKI_DOMAIN": wiki_ctx.active_domain}
    }

    console.print("[bold cyan]Wiki MCP 交互式配置[/bold cyan]\n")

    # Claude Code
    cc_settings = Path.home() / ".claude" / "settings.json"
    if Confirm.ask(f"配置 Claude Code ({cc_settings})?", default=True):
        _write_mcp_config_json(cc_settings, mcp_entry, key="mcpServers")
        console.print(f"[green]✓[/green] Claude Code 配置完成")

    # CodeX CLI
    codex_config = Path.home() / ".codex" / "config.toml"
    if Confirm.ask(f"配置 CodeX CLI ({codex_config})?", default=True):
        _write_mcp_config_toml(codex_config, wiki_bin)
        console.print(f"[green]✓[/green] CodeX CLI 配置完成")

    # Gemini CLI
    gemini_settings = Path.home() / ".gemini" / "settings.json"
    if Confirm.ask(f"配置 Gemini CLI ({gemini_settings})?", default=True):
        _write_mcp_config_json(gemini_settings, {k: v for k, v in mcp_entry.items() if k != "env"}, key="mcpServers")
        console.print(f"[green]✓[/green] Gemini CLI 配置完成")

    console.print("\n[bold green]配置完成！重启 AI 工具后生效。[/bold green]")
    console.print("[dim]提示：运行 wiki mcp start --daemon 启动常驻服务以获得更好性能[/dim]")


def _write_mcp_config_json(config_path: Path, mcp_entry: dict, key: str = "mcpServers"):
    """Merge wiki MCP entry into a JSON config file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    if key not in config:
        config[key] = {}
    config[key]["wiki"] = mcp_entry

    # Backup original (remove old backup first)
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.bak")
        if backup_path.exists():
            backup_path.unlink()
        config_path.rename(backup_path)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _write_mcp_config_toml(config_path: Path, wiki_bin: str):
    """Append wiki MCP entry to CodeX TOML config."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content
    existing = ""
    if config_path.exists():
        existing = config_path.read_text(encoding="utf-8")

    # Remove old wiki entry if exists
    lines = [l for l in existing.splitlines() if not l.startswith("[mcp_servers.wiki]")]
    new_content = "\n".join(lines).rstrip()

    # Append new entry
    wiki_entry = f'\n\n[mcp_servers.wiki]\ncommand = "{wiki_bin}"\nargs = ["mcp", "serve"]\n'
    config_path.write_text(new_content + wiki_entry, encoding="utf-8")
