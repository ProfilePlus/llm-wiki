"""wiki list - List wiki pages."""

import click
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.wiki_fs import iter_wiki_pages
from ..core.page_types import detect_type
from ..output import is_machine_mode, output_json

console = Console()


@click.command("list")
@click.option("--type", "page_type", help="按类型过滤 (summary/entity/concept/...)")
@click.pass_context
def list_pages(ctx, page_type):
    """列出 wiki 页面。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    pages = []
    for p in iter_wiki_pages(wiki_ctx.wiki_path):
        if p.name in ("index.md", "log.md"):
            continue
        pt = detect_type(p)
        if page_type and pt != page_type:
            continue
        pages.append({"path": str(p.relative_to(wiki_ctx.wiki_path)), "type": pt or "other", "slug": p.stem})

    if is_machine_mode():
        output_json({"pages": pages, "count": len(pages)})
        return

    if not pages:
        console.print("[dim]暂无页面[/dim]")
        return

    table = Table(title=f"Wiki 页面 ({len(pages)})")
    table.add_column("Slug", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("路径", style="dim")

    for p in sorted(pages, key=lambda x: x["slug"]):
        table.add_row(p["slug"], p["type"], p["path"])

    console.print(table)
