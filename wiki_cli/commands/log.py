"""wiki log - Show operation log."""

import click
from rich.console import Console

from ..context import WikiContext
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.option("--limit", default=20, help="显示最近 N 条记录")
@click.pass_context
def log(ctx, limit):
    """查看操作日志。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    log_path = wiki_ctx.wiki_path / "log.md"
    if not log_path.exists():
        console.print("[dim]暂无日志[/dim]")
        return

    content = log_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    # Extract log entries (lines starting with ##)
    entries = [line for line in lines if line.startswith("##")]
    recent = entries[-limit:] if len(entries) > limit else entries

    if is_machine_mode():
        output_json({"entries": recent, "total": len(entries)})
        return

    if not recent:
        console.print("[dim]暂无日志条目[/dim]")
        return

    console.print(f"[cyan]最近 {len(recent)} 条操作:[/cyan]\n")
    for entry in recent:
        console.print(entry)
