"""wiki query - Query the wiki."""

import click
from rich.console import Console
from rich.panel import Panel

from ..context import WikiContext
from ..core.query_engine import query_wiki_sync
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.argument("question")
@click.pass_context
def query(ctx, question):
    """查询 wiki。"""
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

    wiki_path = wiki_ctx.wiki_path

    if not is_machine_mode():
        console.print(f"[cyan]查询:[/cyan] {question}")

    try:
        result = query_wiki_sync(question, wiki_path, provider)
    except Exception as e:
        if is_machine_mode():
            output_json({"error": str(e)})
        else:
            console.print(f"[red]查询失败: {e}[/red]")
        return

    if is_machine_mode():
        output_json(result)
        return

    answer = result.get("answer", "")
    console.print(Panel(answer, title="回答", border_style="green"))

    cited = result.get("cited_pages", [])
    if cited:
        console.print(f"\n[dim]参考页面: {', '.join(f'[[{p}]]' for p in cited)}[/dim]")
