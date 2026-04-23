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
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """设置配置项。"""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "key": key, "value": value})
    else:
        console.print(f"[green]✓[/green] {key} = {value}")
