"""wiki provider - Manage LLM providers."""

import click
from rich.console import Console
from rich.table import Table

from ..config import load_config, save_config
from ..output import is_machine_mode, output_json

console = Console()


@click.group()
def provider():
    """管理 LLM provider。"""
    pass


@provider.command("add")
@click.argument("name")
@click.option("--type", "provider_type", type=click.Choice(["anthropic", "openai"]), prompt=True)
@click.option("--api-key", prompt=True, hide_input=True)
@click.option("--model", prompt=True)
@click.option("--base-url", default=None, prompt=False, help="OpenAI 兼容接口的 base_url")
@click.pass_context
def provider_add(ctx, name, provider_type, api_key, model, base_url):
    """添加新的 provider。"""
    config = load_config()

    provider_config = {
        "type": provider_type,
        "api_key": api_key,
        "model": model,
    }
    if base_url:
        provider_config["base_url"] = base_url

    if "providers" not in config:
        config["providers"] = {}
    config["providers"][name] = provider_config

    if not config.get("active_provider"):
        config["active_provider"] = name

    save_config(config)

    if is_machine_mode():
        output_json({"status": "ok", "provider": name, "type": provider_type})
    else:
        console.print(f"[green]✓[/green] Provider [cyan]{name}[/cyan] 已添加")
        if config.get("active_provider") == name:
            console.print(f"[green]✓[/green] 已设为当前活跃 provider")


@provider.command("list")
@click.pass_context
def provider_list(ctx):
    """列出所有 provider。"""
    config = load_config()
    providers = config.get("providers", {})
    active = config.get("active_provider")

    if is_machine_mode():
        output_json({"providers": providers, "active": active})
        return

    if not providers:
        console.print("[yellow]暂无 provider，请运行 wiki provider add <name>[/yellow]")
        return

    table = Table(title="LLM Providers")
    table.add_column("名称", style="cyan")
    table.add_column("类型")
    table.add_column("模型")
    table.add_column("Base URL")
    table.add_column("状态", style="green")

    for name, p in providers.items():
        status = "● 活跃" if name == active else ""
        table.add_row(
            name,
            p.get("type", ""),
            p.get("model", ""),
            p.get("base_url", "-"),
            status,
        )

    console.print(table)


@provider.command("use")
@click.argument("name")
@click.pass_context
def provider_use(ctx, name):
    """切换当前活跃 provider。"""
    config = load_config()

    if name not in config.get("providers", {}):
        console.print(f"[red]Provider {name} 不存在[/red]")
        return

    config["active_provider"] = name
    save_config(config)

    if is_machine_mode():
        output_json({"status": "ok", "active_provider": name})
    else:
        console.print(f"[green]✓[/green] 已切换到 provider: [cyan]{name}[/cyan]")
