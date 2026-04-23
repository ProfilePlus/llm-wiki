"""wiki links/backlinks/orphans/broken - Link analysis commands."""

import click
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.link_parser import build_link_graph, find_backlinks, find_orphans, find_broken
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.argument("page")
@click.pass_context
def links(ctx, page):
    """显示某页的出链。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    graph = build_link_graph(wiki_ctx.wiki_path)
    outlinks = graph.get(page, [])

    if is_machine_mode():
        output_json({"page": page, "links": outlinks, "count": len(outlinks)})
        return

    if not outlinks:
        console.print(f"[dim]{page} 没有出链[/dim]")
        return

    console.print(f"[cyan]{page}[/cyan] 的出链 ({len(outlinks)}):")
    for link in outlinks:
        console.print(f"  → {link}")


@click.command()
@click.argument("page")
@click.pass_context
def backlinks(ctx, page):
    """显示某页的反向链接。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    graph = build_link_graph(wiki_ctx.wiki_path)
    backs = find_backlinks(graph, page)

    if is_machine_mode():
        output_json({"page": page, "backlinks": backs, "count": len(backs)})
        return

    if not backs:
        console.print(f"[dim]{page} 没有反向链接[/dim]")
        return

    console.print(f"[cyan]{page}[/cyan] 的反向链接 ({len(backs)}):")
    for src in backs:
        console.print(f"  ← {src}")


@click.command()
@click.pass_context
def orphans(ctx):
    """找出孤儿页（没有入链的页面）。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    graph = build_link_graph(wiki_ctx.wiki_path)
    orphan_pages = find_orphans(graph)

    if is_machine_mode():
        output_json({"orphans": orphan_pages, "count": len(orphan_pages)})
        return

    if not orphan_pages:
        console.print("[green]✓[/green] 没有孤儿页")
        return

    console.print(f"[yellow]孤儿页 ({len(orphan_pages)}):[/yellow]")
    for p in orphan_pages:
        console.print(f"  • {p}")


@click.command()
@click.pass_context
def broken(ctx):
    """找出断链。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    graph = build_link_graph(wiki_ctx.wiki_path)
    existing = set(graph.keys())
    broken_links = find_broken(graph, existing)

    if is_machine_mode():
        output_json({"broken": [{"source": s, "target": t} for s, t in broken_links], "count": len(broken_links)})
        return

    if not broken_links:
        console.print("[green]✓[/green] 没有断链")
        return

    console.print(f"[red]断链 ({len(broken_links)}):[/red]")
    for src, target in broken_links:
        console.print(f"  {src} → [red]{target}[/red]")
