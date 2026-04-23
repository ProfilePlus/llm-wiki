"""wiki lint - Health check."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..context import WikiContext
from ..core.lint_engine import lint_wiki_sync
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.pass_context
def lint(ctx):
    """运行 wiki 健康检查。"""
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
        console.print("[cyan]正在检查 wiki 健康度...[/cyan]")

    try:
        result = lint_wiki_sync(wiki_path, provider, wiki_ctx.language)
    except Exception as e:
        if is_machine_mode():
            output_json({"error": str(e)})
        else:
            console.print(f"[red]检查失败: {e}[/red]")
        return

    if is_machine_mode():
        output_json(result)
        return

    # Rich display
    stats = result.get("stats", {})
    console.print(f"\n[bold]Wiki 统计[/bold]")
    console.print(f"  总页面: {stats.get('total_pages', 0)}")
    console.print(f"  孤儿页: {stats.get('orphans', 0)}")
    console.print(f"  断链: {stats.get('broken_links', 0)}")

    issues = result.get("issues", [])
    if issues:
        table = Table(title=f"发现 {len(issues)} 个问题")
        table.add_column("严重度", style="yellow")
        table.add_column("类型")
        table.add_column("描述")
        table.add_column("建议", style="dim")

        for issue in issues[:20]:  # Show first 20
            table.add_row(
                issue.get("severity", ""),
                issue.get("type", ""),
                issue.get("description", ""),
                issue.get("suggestion", "")
            )

        console.print(table)
    else:
        console.print("[green]✓ 未发现问题[/green]")

    suggested = result.get("suggested_pages", [])
    if suggested:
        console.print(f"\n[bold]建议新建页面 ({len(suggested)}):[/bold]")
        for s in suggested[:10]:
            console.print(f"  • [{s['type']}] {s['slug']}: {s['reason']}")

    summary = result.get("summary", "")
    if summary:
        console.print(Panel(summary, title="整体评估", border_style="blue"))
