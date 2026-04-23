"""wiki init - Initialize wiki directory structure."""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ..config import load_config, save_config
from ..constants import DEFAULT_DATA_DIR, SUPPORTED_LANGUAGES

console = Console()


@click.command()
@click.option("--path", default=None, help="数据目录路径（默认 D:\\AI\\llm-wiki）")
@click.option("--skip-config", is_flag=True, help="跳过交互式配置")
@click.pass_context
def init(ctx, path, skip_config):
    """初始化 wiki 目录结构和配置文件。"""

    console.print(Panel.fit(
        "[bold cyan]Wiki CLI 初始化向导[/bold cyan]\n"
        "让我们一起完成初始配置",
        border_style="cyan"
    ))
    console.print()

    # 1. Create data directory
    data_dir = Path(path) if path else Path(DEFAULT_DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] 数据目录: {data_dir}")

    # Load or create config
    config = load_config()
    config["data_dir"] = str(data_dir)

    if skip_config:
        save_config(config)
        console.print(f"[green]✓[/green] 配置已保存")
        console.print("\n[yellow]提示：使用 --skip-config 跳过了交互配置[/yellow]")
        console.print("请手动运行以下命令完成配置：")
        console.print("  wiki domain add <name>")
        console.print("  wiki provider add <name>")
        console.print("  wiki language <zh|en>")
        return

    console.print()

    # 2. Configure language
    console.print("[bold]1. 语言配置[/bold]")
    language = Prompt.ask(
        "选择 wiki 语言",
        choices=SUPPORTED_LANGUAGES,
        default="zh"
    )
    config["language"] = language
    console.print(f"[green]✓[/green] 语言: {'中文' if language == 'zh' else 'English'}")
    console.print()

    # 3. Create first domain
    console.print("[bold]2. 创建知识领域[/bold]")
    console.print("[dim]领域用于组织不同类型的知识（如 ai、work、life）[/dim]")

    domain_name = Prompt.ask(
        "第一个领域名称",
        default="ai"
    )

    # Create domain directories
    domain_dir = data_dir / domain_name
    (domain_dir / "raw").mkdir(parents=True, exist_ok=True)
    wiki_dir = domain_dir / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    # Create index.md and log.md
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(
            f"# {domain_name} Wiki Index\n\n> 此文件由 wiki CLI 自动维护。\n",
            encoding="utf-8",
        )

    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        log_path.write_text(
            f"# {domain_name} Wiki Log\n\n> 操作日志，追加写入。\n",
            encoding="utf-8",
        )

    config["active_domain"] = domain_name
    console.print(f"[green]✓[/green] 领域: {domain_name}")
    console.print()

    # 4. Configure LLM provider
    console.print("[bold]3. 配置 LLM Provider[/bold]")
    console.print("[dim]Provider 用于调用 AI 模型进行知识编译[/dim]")

    if not Confirm.ask("现在配置 provider？", default=True):
        save_config(config)
        console.print("\n[yellow]跳过 provider 配置[/yellow]")
        console.print("稍后可运行: wiki provider add <name>")
        show_summary(config, data_dir, domain_name, None)
        return

    provider_name = Prompt.ask(
        "Provider 名称",
        default="claude"
    )

    provider_type = Prompt.ask(
        "Provider 类型",
        choices=["anthropic", "openai"],
        default="anthropic"
    )

    api_key = Prompt.ask(
        "API Key",
        password=True
    )

    model = Prompt.ask(
        "模型名称",
        default="claude-sonnet-4-20250514" if provider_type == "anthropic" else "gpt-4o"
    )

    provider_config = {
        "type": provider_type,
        "api_key": api_key,
        "model": model,
    }

    if provider_type == "openai":
        if Confirm.ask("需要自定义 base_url？（如火山方舟）", default=False):
            base_url = Prompt.ask("Base URL")
            provider_config["base_url"] = base_url

    if "providers" not in config:
        config["providers"] = {}
    config["providers"][provider_name] = provider_config
    config["active_provider"] = provider_name

    console.print(f"[green]✓[/green] Provider: {provider_name} ({provider_type})")
    console.print()

    # Save config
    save_config(config)

    # Show summary
    show_summary(config, data_dir, domain_name, provider_name)


def show_summary(config, data_dir, domain_name, provider_name):
    """Show configuration summary."""
    console.print(Panel.fit(
        "[bold green]✓ 初始化完成！[/bold green]\n\n"
        f"数据目录: {data_dir}\n"
        f"活跃领域: {domain_name}\n"
        f"语言: {'中文' if config.get('language') == 'zh' else 'English'}\n"
        f"Provider: {provider_name or '(未配置)'}\n\n"
        "[bold]现在可以使用:[/bold]\n"
        "  wiki ingest <file> --topic <topic>  [dim]摄入文档[/dim]\n"
        "  wiki query \"<问题>\"                  [dim]查询知识[/dim]\n"
        "  wiki lint                           [dim]健康检查[/dim]",
        border_style="green"
    ))

