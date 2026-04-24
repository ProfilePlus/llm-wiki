"""wiki config - View and set configuration."""

import click
from pathlib import Path
from rich.console import Console

from ..config import load_config, save_config
from ..output import is_machine_mode, output_json
from ..constants import SUPPORTED_LANGUAGES

console = Console()


def _get_config_options(cfg, key):
    """获取配置项的可选值列表"""
    if key == "language":
        return [("zh", "中文"), ("en", "English")]
    elif key == "active_domain":
        data_dir = Path(cfg.get("data_dir", ""))
        if not data_dir.exists():
            return []
        domains = [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return [(d, d) for d in sorted(domains)]
    elif key == "active_provider":
        providers = list(cfg.get("providers", {}).keys())
        return [(p, p) for p in sorted(providers)]
    elif key == "data_dir":
        return None  # 文本输入
    return []


def _run_config_tui(cfg):
    """运行多级 TUI 配置界面"""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.formatted_text import HTML

    # 状态
    config_keys = ["data_dir", "language", "active_domain", "active_provider"]
    current_tab = 0  # 当前标签索引
    cursor_pos = 0   # 子选项光标位置
    modified = {k: False for k in config_keys}  # 是否修改过
    selections = {k: cfg.get(k) for k in config_keys}  # 当前选中值
    text_buffer = {k: str(cfg.get(k, "")) for k in config_keys}  # data_dir 的文本缓冲

    def get_title_bar():
        return HTML("<b>配置面板</b>  ← → 切换标签  空格勾选  Enter确定")

    def get_tab_bar():
        tabs = []
        for i, key in enumerate(config_keys):
            check = "☑" if modified[key] else "☐"
            if i == current_tab:
                tabs.append(f"<b><style bg='#5f87ff' fg='white'> {check} {key} </style></b>")
            else:
                tabs.append(f" {check} {key} ")
        return HTML("".join(tabs))

    def get_options_area():
        key = config_keys[current_tab]
        options = _get_config_options(cfg, key)
        lines = [f"▼ {key} - 子选项\n"]

        if options is None:  # data_dir 文本输入
            lines.append(f"  文本输入: {text_buffer[key]}")
            lines.append("  (输入字符修改，Backspace 删除)")
        elif not options:
            lines.append("  (无可选项)")
        else:
            for i, (value, label) in enumerate(options):
                pointer = "❯ " if i == cursor_pos else "  "
                check = "◉" if selections[key] == value else "○"
                lines.append(f"  {pointer}{check} {label}")

        return "\n".join(lines)

    def get_status_bar():
        modified_count = sum(1 for v in modified.values() if v)
        return f" 已修改: {modified_count} 项 ｜ Esc 退出 "

    # 布局
    title_window = Window(content=FormattedTextControl(get_title_bar), height=1)
    tab_window = Window(content=FormattedTextControl(get_tab_bar), height=1)
    options_window = Window(content=FormattedTextControl(get_options_area), height=10)
    status_window = Window(content=FormattedTextControl(get_status_bar), height=1)

    root_container = HSplit([
        Window(char="─", height=1),
        title_window,
        Window(char="─", height=1),
        tab_window,
        Window(char="─", height=1),
        options_window,
        Window(char="─", height=1),
        status_window,
        Window(char="─", height=1),
    ])

    layout = Layout(root_container)

    # 键盘绑定
    kb = KeyBindings()

    @kb.add("left")
    def _(event):
        nonlocal current_tab, cursor_pos
        current_tab = (current_tab - 1) % len(config_keys)
        cursor_pos = 0

    @kb.add("right")
    def _(event):
        nonlocal current_tab, cursor_pos
        current_tab = (current_tab + 1) % len(config_keys)
        cursor_pos = 0

    @kb.add("up")
    def _(event):
        nonlocal cursor_pos
        key = config_keys[current_tab]
        options = _get_config_options(cfg, key)
        if options and len(options) > 0:
            cursor_pos = (cursor_pos - 1) % len(options)

    @kb.add("down")
    def _(event):
        nonlocal cursor_pos
        key = config_keys[current_tab]
        options = _get_config_options(cfg, key)
        if options and len(options) > 0:
            cursor_pos = (cursor_pos + 1) % len(options)

    @kb.add("space")
    def _(event):
        key = config_keys[current_tab]
        options = _get_config_options(cfg, key)
        if options and len(options) > 0:
            value, _ = options[cursor_pos]
            selections[key] = value
            modified[key] = True

    @kb.add("c-c")
    @kb.add("escape")
    def _(event):
        event.app.exit(result=None)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=selections)

    # data_dir 文本输入
    @kb.add("<any>")
    def _(event):
        key = config_keys[current_tab]
        if key == "data_dir":
            char = event.data
            if char and char.isprintable():
                text_buffer[key] += char
                selections[key] = text_buffer[key]
                modified[key] = True

    @kb.add("c-h")  # Backspace
    def _(event):
        key = config_keys[current_tab]
        if key == "data_dir" and text_buffer[key]:
            text_buffer[key] = text_buffer[key][:-1]
            selections[key] = text_buffer[key]
            modified[key] = True

    app = Application(layout=layout, key_bindings=kb, full_screen=False, mouse_support=False)
    result = app.run()

    if result is None:
        return None

    # 只返回被修改的项
    return {k: v for k, v in result.items() if modified[k]}


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

    # 如果提供了 key 和 value，直接设置
    if key and value is not None:
        cfg[key] = value
        save_config(cfg)
        if is_machine_mode():
            output_json({"status": "ok", "key": key, "value": value})
        else:
            console.print(f"[green]✓[/green] {key} = {value}")
        return

    # 交互模式：启动 TUI
    updated = _run_config_tui(cfg)

    if updated is None:
        console.print("[yellow]已取消[/yellow]")
        return

    if not updated:
        console.print("[yellow]未修改任何配置项[/yellow]")
        return

    # 保存修改
    for k, v in updated.items():
        cfg[k] = v
    save_config(cfg)

    if is_machine_mode():
        output_json({"status": "ok", "updated": updated})
    else:
        console.print(f"[green]✓[/green] 已更新 {len(updated)} 项配置:")
        for k, v in updated.items():
            console.print(f"  • {k} = {v}")
