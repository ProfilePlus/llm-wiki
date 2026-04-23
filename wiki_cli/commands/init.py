"""wiki init - Initialize wiki directory structure."""

import click
from rich.console import Console

from ..config import load_config, save_config
from ..constants import DEFAULT_DATA_DIR

console = Console()


@click.command()
@click.option("--path", default=None, help="数据目录路径（默认 D:\\AI\\llm-wiki）")
@click.pass_context
def init(ctx, path):
    """初始化 wiki 目录结构和配置文件。"""
    from pathlib import Path

    data_dir = Path(path) if path else Path(DEFAULT_DATA_DIR)

    # Create base directory
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize config
    config = load_config()
    config["data_dir"] = str(data_dir)
    save_config(config)

    console.print(f"[green]✓[/green] 数据目录已创建: {data_dir}")
    console.print(f"[green]✓[/green] 配置文件已保存: ~/.wiki/config.json")
    console.print()
    console.print("[dim]下一步:[/dim]")
    console.print("  wiki domain add ai       [dim]创建第一个领域[/dim]")
    console.print("  wiki provider add claude  [dim]配置 LLM provider[/dim]")
