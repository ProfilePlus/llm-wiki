"""wiki ingest - Ingest source file into wiki."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.ingest_engine import ingest_file_sync
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--topic", required=True, help="topic 目录名")
@click.pass_context
def ingest(ctx, source, topic):
    """摄入源文档到 wiki。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]错误：未设置活跃领域。运行 wiki domain use <name>[/red]")
        return

    if not wiki_ctx.active_provider:
        console.print("[red]错误：未设置活跃 provider。运行 wiki provider use <name>[/red]")
        return

    try:
        provider = wiki_ctx.create_provider()
    except Exception as e:
        console.print(f"[red]Provider 初始化失败: {e}[/red]")
        return

    source_path = Path(source)
    domain_path = wiki_ctx.domain_path

    if not is_machine_mode():
        console.print(f"[cyan]正在摄入[/cyan] {source_path.name} → topic: {topic}...")

    try:
        result = ingest_file_sync(source_path, topic, domain_path, provider, wiki_ctx.language)
    except Exception as e:
        if is_machine_mode():
            output_json({"error": str(e)})
        else:
            console.print(f"[red]摄入失败: {e}[/red]")
        return

    if "error" in result:
        if is_machine_mode():
            output_json(result)
        else:
            console.print(f"[red]错误: {result['error']}[/red]")
        return

    if is_machine_mode():
        output_json(result)
        return

    # Rich display
    console.print(f"[green]✓[/green] 摄入完成")
    console.print(f"  Raw: {result['raw_path']}")
    console.print()

    if result["created"]:
        table = Table(title=f"创建的页面 ({len(result['created'])})")
        table.add_column("路径", style="cyan")
        for p in result["created"]:
            table.add_row(p)
        console.print(table)

    if result["updated"]:
        table = Table(title=f"更新的页面 ({len(result['updated'])})")
        table.add_column("路径", style="yellow")
        for p in result["updated"]:
            table.add_row(p)
        console.print(table)

    console.print(f"\n[dim]{result['log_entry']}[/dim]")
