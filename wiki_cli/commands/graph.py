"""wiki graph - Export link graph as JSON."""

import click

from ..context import WikiContext
from ..core.link_parser import build_link_graph
from ..output import output_json

from rich.console import Console

console = Console()


@click.command()
@click.pass_context
def graph(ctx):
    """导出链接关系图（JSON）。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    g = build_link_graph(wiki_ctx.wiki_path)
    output_json({"graph": g, "nodes": len(g), "edges": sum(len(v) for v in g.values())})
