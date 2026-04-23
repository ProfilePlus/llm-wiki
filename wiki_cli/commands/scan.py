"""wiki scan - Scan raw/ for unprocessed files."""

import click
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.wiki_fs import iter_raw_files
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.pass_context
def scan(ctx):
    """扫描 raw/ 中的文件。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.raw_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    files = list(iter_raw_files(wiki_ctx.raw_path))

    if is_machine_mode():
        output_json({"files": [str(f) for f in files], "count": len(files)})
        return

    if not files:
        console.print("[dim]raw/ 中暂无文件[/dim]")
        return

    table = Table(title=f"Raw 文件 ({len(files)})")
    table.add_column("文件名", style="cyan")
    table.add_column("大小")
    table.add_column("类型")

    for f in files:
        size = f.stat().st_size
        size_str = f"{size // 1024}KB" if size > 1024 else f"{size}B"
        table.add_row(f.name, size_str, f.suffix)

    console.print(table)
