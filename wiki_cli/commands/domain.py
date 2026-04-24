"""wiki domain - Manage knowledge domains."""

import click
from rich.console import Console
from rich.table import Table

from ..config import load_config, save_config
from ..output import is_machine_mode, output_json

console = Console()


@click.group()
def domain():
    """管理知识领域（ai / work / life ...）。"""
    pass


@domain.command("add")
@click.argument("name", required=False)
@click.pass_context
def domain_add(ctx, name):
    """创建新领域。"""
    if not name:
        name = click.prompt("领域名称 (如 ai / work / life)").strip()
    if not name:
        console.print("[red]领域名称不能为空[/red]")
        return
    """创建新领域。"""
    from pathlib import Path

    config = load_config()
    data_dir = Path(config["data_dir"])
    domain_dir = data_dir / name

    # Create raw/ and wiki/ structure
    (domain_dir / "raw").mkdir(parents=True, exist_ok=True)
    wiki_dir = domain_dir / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    # Create index.md and log.md
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(
            f"# {name} Wiki Index\n\n> 此文件由 wiki CLI 自动维护。\n",
            encoding="utf-8",
        )

    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        log_path.write_text(
            f"# {name} Wiki Log\n\n> 操作日志，追加写入。\n",
            encoding="utf-8",
        )

    # Set as active domain if none set
    if not config.get("active_domain"):
        config["active_domain"] = name
        save_config(config)

    if is_machine_mode():
        output_json({"status": "ok", "domain": name, "path": str(domain_dir)})
    else:
        console.print(f"[green]✓[/green] 领域 [cyan]{name}[/cyan] 已创建: {domain_dir}")
        if config.get("active_domain") == name:
            console.print(f"[green]✓[/green] 已设为当前活跃领域")


@domain.command("list")
@click.pass_context
def domain_list(ctx):
    """列出所有领域。"""
    from pathlib import Path

    config = load_config()
    data_dir = Path(config["data_dir"])
    active = config.get("active_domain")

    if not data_dir.exists():
        console.print("[yellow]数据目录不存在，请先运行 wiki init[/yellow]")
        return

    domains = [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if is_machine_mode():
        output_json({"domains": domains, "active": active})
        return

    if not domains:
        console.print("[yellow]暂无领域，请运行 wiki domain add <name>[/yellow]")
        return

    table = Table(title="知识领域")
    table.add_column("名称", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("Wiki 页面数")
    table.add_column("Raw 文档数")

    for d in sorted(domains):
        status = "● 活跃" if d == active else ""
        wiki_count = len(list((data_dir / d / "wiki").rglob("*.md"))) if (data_dir / d / "wiki").exists() else 0
        raw_count = len(list((data_dir / d / "raw").rglob("*.md"))) if (data_dir / d / "raw").exists() else 0
        table.add_row(d, status, str(wiki_count), str(raw_count))

    console.print(table)


@domain.command("use")
@click.argument("name")
@click.pass_context
def domain_use(ctx, name):
    """切换当前活跃领域。"""
    from pathlib import Path

    config = load_config()
    data_dir = Path(config["data_dir"])

    if not (data_dir / name).exists():
        console.print(f"[red]领域 {name} 不存在[/red]")
        return

    config["active_domain"] = name
    save_config(config)

    if is_machine_mode():
        output_json({"status": "ok", "active_domain": name})
    else:
        console.print(f"[green]✓[/green] 已切换到领域: [cyan]{name}[/cyan]")
