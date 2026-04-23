"""Main CLI entry point with ASCII welcome screen."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .constants import LOGO
from .context import WikiContext

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Local LLM Wiki - Karpathy's compiled wiki pattern."""
    # Create context
    ctx.obj = WikiContext()

    # If no subcommand, show welcome screen
    if ctx.invoked_subcommand is None:
        show_welcome(ctx.obj)


def show_welcome(wiki_ctx: WikiContext):
    """Show ASCII logo and status dashboard."""
    # Logo
    console.print(Text(LOGO, style="bold cyan"))
    console.print(Text(f"Local LLM Wiki v{__version__}", style="dim"))
    console.print()

    # Status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    domain = wiki_ctx.active_domain or "(未设置)"
    provider = wiki_ctx.active_provider or "(未设置)"
    data_dir = str(wiki_ctx.data_dir)

    # Count pages if domain exists
    pages_count = "N/A"
    raw_count = "N/A"
    if wiki_ctx.wiki_path and wiki_ctx.wiki_path.exists():
        pages_count = len(list(wiki_ctx.wiki_path.rglob("*.md")))
    if wiki_ctx.raw_path and wiki_ctx.raw_path.exists():
        raw_count = len(list(wiki_ctx.raw_path.rglob("*.md")))

    table.add_row("Domain", domain)
    table.add_row("Provider", provider)
    table.add_row("Language", "中文" if wiki_ctx.language == "zh" else "English")
    table.add_row("Data Dir", data_dir)
    table.add_row("Pages", str(pages_count))
    table.add_row("Raw Docs", str(raw_count))

    console.print(table)
    console.print()

    # Commands hint
    console.print(Text("常用命令：", style="bold"))
    console.print("  [cyan]wiki init[/cyan]           [dim]初始化 wiki[/dim]")
    console.print("  [cyan]wiki ingest <file>[/cyan]  [dim]摄入源文档[/dim]")
    console.print("  [cyan]wiki query \"问题\"[/cyan]   [dim]查询 wiki[/dim]")
    console.print("  [cyan]wiki lint[/cyan]           [dim]健康检查[/dim]")
    console.print("  [cyan]wiki status[/cyan]         [dim]详细状态[/dim]")


# Register commands
from .commands.init import init
from .commands.domain import domain
from .commands.provider import provider
from .commands.config_cmd import config
from .commands.status import status
from .commands.scan import scan
from .commands.list_pages import list_pages
from .commands.links import links, backlinks, orphans, broken
from .commands.index_cmd import index_cmd
from .commands.graph import graph
from .commands.stats import stats
from .commands.log import log
from .commands.ingest import ingest
from .commands.query import query
from .commands.lint import lint
from .commands.language import language

cli.add_command(init)
cli.add_command(domain)
cli.add_command(provider)
cli.add_command(config)
cli.add_command(status)
cli.add_command(scan)
cli.add_command(list_pages)
cli.add_command(links)
cli.add_command(backlinks)
cli.add_command(orphans)
cli.add_command(broken)
cli.add_command(index_cmd)
cli.add_command(graph)
cli.add_command(stats)
cli.add_command(log)
cli.add_command(ingest)
cli.add_command(query)
cli.add_command(lint)
cli.add_command(language)


if __name__ == "__main__":
    cli()
