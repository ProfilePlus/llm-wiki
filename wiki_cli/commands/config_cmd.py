"""wiki config - View and set configuration."""

import click
from rich.console import Console

from ..config import load_config, save_config
from ..output import is_machine_mode, output_json

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """查看或修改配置。"""
    if ctx.invoked_subcommand is None:
        cfg = load_config()
        safe_cfg = cfg.copy()
        for name, p in safe_cfg.get("providers", {}).items():
            if "api_key" in p:
                safe_cfg["providers"][name] = {**p, "api_key": p["api_key"][:8] + "..."}

        if is_machine_mode():
            output_json(safe_cfg)
        else:
            import json
            console.print_json(json.dumps(safe_cfg, ensure_ascii=False))


@config.command("set")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_set(key, value):
    """设置配置项。"""
    cfg = load_config()
    if not key:
        keys = [k for k in cfg.keys() if k != "providers"]
        console.print("[bold]可配置项:[/bold]")
        for i, k in enumerate(keys, 1):
            cur = cfg.get(k, "")
            console.print(f"  [cyan]{i}[/cyan]. {k} [dim]= {cur}[/dim]")
        console.print(f"  [cyan]{len(keys)+1}[/cyan]. [dim]手动输入其他键名[/dim]")
        choice = click.prompt("选择", type=click.IntRange(1, len(keys)+1), default=1)
        if choice <= len(keys):
            key = keys[choice-1]
        else:
            key = click.prompt("配置项名称").strip()
    if value is None:
        current = cfg.get(key, "")
        value = click.prompt(f"{key} 的值", default=str(current) if current else None)
    cfg[key] = value
    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "key": key, "value": value})
    else:
        console.print(f"[green]✓[/green] {key} = {value}")
