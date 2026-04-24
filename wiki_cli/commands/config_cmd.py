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
    cfg = load_config()

    # 如果提供了 key 和 value，直接设置
    if key and value is not None:
        cfg[key] = value
        save_config(cfg)
        if is_machine_mode():
            output_json({"status": "ok", "key": key, "value": value})
        else:
            console.print(f"[green]✓[/green] {key} = {value}")
        return

    # 交互模式：多选要修改的配置项
    keys = [k for k in cfg.keys() if k != "providers"]
    width = max(len(k) for k in keys) + 2
    choices = [
        Choice(value=k, name=f"{k:<{width}}  →  {cfg.get(k,'')}", enabled=False)
        for k in keys
    ]

    selected_keys = inquirer.checkbox(
        message="选择要修改的配置项 (空格选中, Enter 确认):",
        choices=choices,
        qmark="▸",
        amark="✓",
        pointer="❯",
        instruction="(↑↓ 移动, 空格 选中/取消, Enter 确认)",
        border=True,
        cycle=True,
        style={"border": "fg:#5f87ff"},
        transformer=lambda result: f"{len(result)} 项已选",
    ).execute()

    if not selected_keys:
        console.print("[yellow]未选择任何配置项[/yellow]")
        return

    # 逐一输入新值
    updated = {}
    for k in selected_keys:
        current = cfg.get(k, "")
        new_value = inquirer.text(
            message=f"{k} 的新值:",
            default=str(current) if current else "",
            qmark="▸",
        ).execute()
        if new_value is not None:
            cfg[k] = new_value
            updated[k] = new_value

    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "updated": updated})
    else:
        console.print(f"[green]✓[/green] 已更新 {len(updated)} 项配置:")
        for k, v in updated.items():
            console.print(f"  • {k} = {v}")
