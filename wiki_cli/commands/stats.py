"""wiki stats - Show wiki statistics."""

import click
from rich.console import Console
from rich.table import Table

from ..context import WikiContext
from ..core.wiki_fs import iter_wiki_pages, iter_raw_files
from ..core.page_types import type_counts
from ..core.link_parser import build_link_graph, find_orphans, find_broken
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.pass_context
def stats(ctx):
    """显示 wiki 统计信息。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    wiki_pages = list(iter_wiki_pages(wiki_ctx.wiki_path))
    raw_files = list(iter_raw_files(wiki_ctx.raw_path)) if wiki_ctx.raw_path else []
    counts = type_counts(wiki_ctx.wiki_path)
    graph = build_link_graph(wiki_ctx.wiki_path)
    orphan_list = find_orphans(graph)
    existing = set(graph.keys())
    broken_list = find_broken(graph, existing)
    total_links = sum(len(v) for v in graph.values())

    # Count topics
    topics = set()
    for p in wiki_pages:
        rel = p.relative_to(wiki_ctx.wiki_path)
        if rel.parent.as_posix() != ".":
            topics.add(rel.parent.as_posix())

    data = {
        "domain": wiki_ctx.active_domain,
        "wiki_pages": len(wiki_pages),
        "raw_files": len(raw_files),
        "topics": len(topics),
        "page_types": counts,
        "total_links": total_links,
        "orphans": len(orphan_list),
        "broken_links": len(broken_list),
    }

    if is_machine_mode():
        output_json(data)
        return

    table = Table(title=f"{wiki_ctx.active_domain} Wiki 统计")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="white")

    table.add_row("Wiki 页面", str(len(wiki_pages)))
    table.add_row("Raw 文档", str(len(raw_files)))
    table.add_row("Topic 数", str(len(topics)))
    table.add_row("总链接数", str(total_links))
    table.add_row("孤儿页", str(len(orphan_list)))
    table.add_row("断链", str(len(broken_list)))

    console.print(table)
    console.print()

    # Page type breakdown
    type_table = Table(title="页面类型分布")
    type_table.add_column("类型", style="cyan")
    type_table.add_column("数量", style="white")
    for pt, count in counts.items():
        if count > 0:
            type_table.add_row(pt, str(count))
    console.print(type_table)
