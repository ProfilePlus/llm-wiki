"""wiki language - View and set wiki language."""

import click
from rich.console import Console

from ..config import load_config, save_config
from ..constants import SUPPORTED_LANGUAGES
from ..output import is_machine_mode, output_json

console = Console()


@click.command()
@click.argument("lang", required=False, type=click.Choice(SUPPORTED_LANGUAGES))
@click.pass_context
def language(ctx, lang):
    """查看或设置 wiki 语言（zh/en）。"""
    config = load_config()
    current = config.get("language", "zh")

    if lang is None:
        if is_machine_mode():
            output_json({"language": current, "supported": SUPPORTED_LANGUAGES})
            return
        console.print(f"当前语言: [cyan]{current}[/cyan]")
        lang = click.prompt("设置语言", type=click.Choice(SUPPORTED_LANGUAGES), default=current)
        if lang == current:
            return

    # Set language
    config["language"] = lang
    save_config(config)

    if is_machine_mode():
        output_json({"status": "ok", "language": lang})
    else:
        lang_name = "中文" if lang == "zh" else "English"
        console.print(f"[green]✓[/green] 语言已设置为: [cyan]{lang_name} ({lang})[/cyan]")
        console.print("[dim]后续所有 AI 操作（ingest/query/lint）将使用此语言[/dim]")
