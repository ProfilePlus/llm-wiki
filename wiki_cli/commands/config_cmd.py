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
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from InquirerPy.separator import Separator
    cfg = load_config()
    if not key:
        keys = [k for k in cfg.keys() if k != "providers"]
        width = max(len(k) for k in keys) + 2
        choices = [
            Choice(value=k, name=f"{k:<{width}}  →  {cfg.get(k,'')}")
            for k in keys
        ] + [Separator(line="─" * 40), Choice(value="__other__", name="✎  手动输入其他键名")]
        key = inquirer.select(
            message="选择要修改的配置项:",
            choices=choices,
            default=keys[0],
            qmark="▸",
            amark="✓",
            pointer="❯",
            instruction="(↑↓ 选择, Enter 确认, Ctrl-C 取消)",
            border=True,
            cycle=True,
            style={"border": "fg:#5f87ff"},
        ).execute()
        if key is None:
            return
        if key == "__other__":
            key = inquirer.text(message="配置项名称:", qmark="▸").execute()
            if not key:
                return
    if value is None:
        current = cfg.get(key, "")
        value = inquirer.text(
            message=f"{key} 的值:",
            default=str(current) if current else "",
            qmark="▸",
        ).execute()
        if value is None:
            return
    cfg[key] = value
    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "key": key, "value": value})
    else:
        console.print(f"[green]✓[/green] {key} = {value}")
