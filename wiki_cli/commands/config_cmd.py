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
    import questionary
    cfg = load_config()
    if not key:
        keys = [k for k in cfg.keys() if k != "providers"]
        choices = [questionary.Choice(f"{k}  [dim]{cfg.get(k,'')}[/dim]", value=k) for k in keys] + [questionary.Choice("手动输入其他键名", value="__other__")]
        key = questionary.select("选择配置项", choices=choices).ask()
        if key is None:
            return
        if key == "__other__":
            key = questionary.text("配置项名称").ask()
            if not key:
                return
    if value is None:
        current = cfg.get(key, "")
        value = questionary.text(f"{key} 的值", default=str(current) if current else "").ask()
        if value is None:
            return
    cfg[key] = value
    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "key": key, "value": value})
    else:
        console.print(f"[green]✓[/green] {key} = {value}")
