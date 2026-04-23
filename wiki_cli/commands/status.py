"""wiki status - Show detailed status dashboard."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..context import WikiContext
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.option("--json", "json_mode", is_flag=True, help="输出 JSON 格式")
@click.pass_context
def status(ctx, json_mode):
    """显示详细状态面板。"""
    wiki_ctx: WikiContext = ctx.obj

    data = {
        "data_dir": str(wiki_ctx.data_dir),
        "active_domain": wiki_ctx.active_domain,
        "active_provider": wiki_ctx.active_provider,
    }

    if wiki_ctx.wiki_path and wiki_ctx.wiki_path.exists():
        data["wiki_pages"] = len(list(wiki_ctx.wiki_path.rglob("*.md")))
    else:
        data["wiki_pages"] = 0

    if wiki_ctx.raw_path and wiki_ctx.raw_path.exists():
        data["raw_docs"] = len(list(wiki_ctx.raw_path.rglob("*.md")))
    else:
        data["raw_docs"] = 0

    if json_mode or is_machine_mode():
        output_json(data)
        return

    # Rich display
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan bold", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("数据目录", data["data_dir"])
    table.add_row("当前领域", data["active_domain"] or "(未设置)")
    table.add_row("当前 Provider", data["active_provider"] or "(未设置)")
    table.add_row("Wiki 页面数", str(data["wiki_pages"]))
    table.add_row("Raw 文档数", str(data["raw_docs"]))

    console.print(Panel(table, title="Wiki 状态", border_style="blue"))
