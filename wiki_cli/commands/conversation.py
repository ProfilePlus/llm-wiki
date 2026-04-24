"""wiki conversation - 同步 Claude Code 对话到 wiki。"""

import click
import json
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress

from ..context import WikiContext

console = Console()


def _get_conversation_domain(wiki_ctx: WikiContext) -> Path:
    """获取对话专用 domain 路径，不存在则自动创建"""
    conv_domain = wiki_ctx.data_dir / "conversations"
    (conv_domain / "raw").mkdir(parents=True, exist_ok=True)
    wiki_dir = conv_domain / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(
            "# Conversations Wiki Index\n\n> AI 工具对话记录，自动收录。\n",
            encoding="utf-8",
        )

    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        log_path.write_text(
            "# Conversations Wiki Log\n\n> 操作日志。\n",
            encoding="utf-8",
        )

    return conv_domain


@click.group()
def conversation():
    """对话同步命令。"""
    pass


@conversation.command()
@click.option("--tool", type=click.Choice(["cc", "codex", "gemini", "all"]), default="all", help="导入哪个工具的对话")
@click.option("--dry-run", is_flag=True, help="预览模式，不实际导入")
@click.option("--min-messages", default=5, help="最少消息数，低于此数的对话跳过")
@click.option("--limit", default=0, help="最多导入几个对话（0=不限）")
@click.pass_context
def import_all(ctx, tool, dry_run, min_messages, limit):
    """一次性导入所有历史对话到 wiki（首次使用）。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.data_dir:
        console.print("[red]错误: 未初始化，请先运行 wiki init[/red]")
        return

    conv_domain = _get_conversation_domain(wiki_ctx)

    # 查找对话历史目录
    tools_to_scan = []
    if tool in ["cc", "all"]:
        cc_dir = Path.home() / ".claude" / "projects"
        if cc_dir.exists():
            tools_to_scan.append(("Claude Code", cc_dir, "cc", "cc-conversations"))

    if tool in ["codex", "all"]:
        codex_dir = Path.home() / ".codex" / "sessions"
        if codex_dir.exists():
            tools_to_scan.append(("CodeX", codex_dir, "codex", "codex-conversations"))

    if tool in ["gemini", "all"]:
        pass

    if not tools_to_scan:
        console.print("[red]错误: 未找到任何对话历史目录[/red]")
        return

    # 加载已处理记录
    sync_record_path = Path.home() / ".wiki" / "conversation_sync.json"
    processed_files = set()
    if sync_record_path.exists():
        with open(sync_record_path, "r", encoding="utf-8") as f:
            processed_files = set(json.load(f).get("processed", []))

    all_conversations = []
    skipped = 0

    console.print("[cyan]正在扫描所有历史对话...[/cyan]")

    for tool_name, tool_dir, tool_key, topic in tools_to_scan:
        console.print(f"  扫描 {tool_name}...")
        for jsonl_file in tool_dir.rglob("*.jsonl"):
            file_key = str(jsonl_file)
            if file_key in processed_files:
                continue

            conv = _parse_conversation(jsonl_file) if tool_key == "cc" else _parse_codex_conversation(jsonl_file)
            if conv and conv["messages"]:
                if len(conv["messages"]) < min_messages:
                    skipped += 1
                    continue
                conv["tool"] = tool_name
                conv["topic"] = topic
                all_conversations.append(conv)

    if not all_conversations:
        console.print("[yellow]未找到新的对话（可能已全部导入）[/yellow]")
        if skipped:
            console.print(f"[dim]跳过 {skipped} 个短对话（< {min_messages} 条消息）[/dim]")
        return

    # 按消息数降序排列（优先导入内容多的对话）
    all_conversations.sort(key=lambda c: len(c["messages"]), reverse=True)

    if limit > 0:
        all_conversations = all_conversations[:limit]

    console.print(f"[green]找到 {len(all_conversations)} 个待导入对话[/green]")
    if skipped:
        console.print(f"[dim]跳过 {skipped} 个短对话（< {min_messages} 条消息）[/dim]")

    if dry_run:
        from rich.table import Table
        table = Table(title="待导入对话")
        table.add_column("工具", style="cyan")
        table.add_column("对话 ID", style="white")
        table.add_column("消息数", style="yellow")
        table.add_column("时间", style="dim")

        for conv in all_conversations[:20]:
            table.add_row(
                conv["tool"],
                conv["id"][:40],
                str(len(conv["messages"])),
                conv["date"]
            )

        console.print(table)
        if len(all_conversations) > 20:
            console.print(f"[dim]...还有 {len(all_conversations) - 20} 个对话[/dim]")
        console.print("\n[dim]去掉 --dry-run 执行实际导入[/dim]")
        return

    # 确认导入
    console.print(f"\n[yellow]即将导入 {len(all_conversations)} 个对话。[/yellow]")
    if not click.confirm("确认继续？", default=True):
        console.print("[yellow]已取消[/yellow]")
        return

    # 批量导入
    imported = []
    failed = []

    with Progress() as progress:
        task = progress.add_task("[cyan]导入中...", total=len(all_conversations))

        for conv in all_conversations:
            try:
                result = _sync_conversation_to_wiki(conv, wiki_ctx)
                if result:
                    imported.append(conv["file"])
                    processed_files.add(conv["file"])
                else:
                    failed.append(conv["id"])
            except Exception as e:
                console.print(f"\n[red]导入失败 {conv['id'][:20]}: {e}[/red]")
                failed.append(conv["id"])

            progress.update(task, advance=1)

            # 每成功导入一个就保存记录（防止中断丢失进度）
            if len(imported) % 5 == 0:
                sync_record_path.parent.mkdir(parents=True, exist_ok=True)
                with open(sync_record_path, "w", encoding="utf-8") as f:
                    json.dump({"processed": list(processed_files)}, f, ensure_ascii=False)

    # 最终保存
    sync_record_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sync_record_path, "w", encoding="utf-8") as f:
        json.dump({"processed": list(processed_files)}, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]✓[/green] 成功导入 {len(imported)} 个对话")
    if failed:
        console.print(f"[red]✗[/red] 失败 {len(failed)} 个")


@conversation.command()
@click.option("--hours", default=1, help="同步最近 N 小时的对话")
@click.option("--dry-run", is_flag=True, help="预览模式，不实际同步")
@click.pass_context
def sync(ctx, hours, dry_run):
    """同步最近的 Claude Code 对话到 wiki。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.data_dir:
        console.print("[red]错误: 未初始化，请先运行 wiki init[/red]")
        return

    claude_projects_dir = Path.home() / ".claude" / "projects"
    if not claude_projects_dir.exists():
        console.print("[red]错误: 未找到 Claude Code 对话目录[/red]")
        return

    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_conversations = []

    console.print(f"[cyan]正在扫描最近 {hours} 小时的对话...[/cyan]")

    for jsonl_file in claude_projects_dir.rglob("*.jsonl"):
        if jsonl_file.stat().st_mtime < cutoff_time.timestamp():
            continue
        conv = _parse_conversation(jsonl_file)
        if conv and conv["messages"]:
            conv["topic"] = "cc-conversations"
            recent_conversations.append(conv)

    if not recent_conversations:
        console.print("[yellow]未找到最近的对话[/yellow]")
        return

    console.print(f"[green]找到 {len(recent_conversations)} 个对话[/green]")

    if dry_run:
        for conv in recent_conversations:
            console.print(f"\n[bold]{conv['id']}[/bold]")
            console.print(f"  消息数: {len(conv['messages'])}")
            console.print(f"  时间: {conv['date']}")
        console.print("\n[dim]去掉 --dry-run 执行实际同步[/dim]")
        return

    with Progress() as progress:
        task = progress.add_task("[cyan]同步中...", total=len(recent_conversations))
        for conv in recent_conversations:
            _sync_conversation_to_wiki(conv, wiki_ctx)
            progress.update(task, advance=1)

    console.print(f"[green]✓[/green] 已同步 {len(recent_conversations)} 个对话")


def _parse_conversation(jsonl_file: Path) -> dict:
    """解析 Claude Code 对话文件"""
    messages = []
    session_id = None

    try:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg_type = data.get("type")

                    if msg_type == "permission-mode":
                        session_id = data.get("sessionId")
                    elif msg_type == "user":
                        content = data.get("message", {}).get("content", "")
                        if content:
                            messages.append({"role": "user", "content": content})
                    elif msg_type == "assistant":
                        content = data.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            text_parts = [
                                item.get("text", "")
                                for item in content
                                if item.get("type") == "text"
                            ]
                            content = "\n".join(text_parts)
                        if content:
                            messages.append({"role": "assistant", "content": content})
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        console.print(f"[red]解析失败 {jsonl_file.name}: {e}[/red]")
        return None

    if not messages:
        return None

    return {
        "id": session_id or jsonl_file.stem,
        "file": str(jsonl_file),
        "messages": messages,
        "date": datetime.fromtimestamp(jsonl_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    }


def _parse_codex_conversation(jsonl_file: Path) -> dict:
    """解析 CodeX 对话文件"""
    messages = []
    session_id = None

    try:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg_type = data.get("type")

                    if msg_type == "session_meta":
                        session_id = data.get("payload", {}).get("id")

                    elif msg_type == "event_msg":
                        payload = data.get("payload", {})
                        event_type = payload.get("type")

                        if event_type == "user_message":
                            content = payload.get("message", "")
                            if content:
                                messages.append({"role": "user", "content": content})

                        elif event_type == "assistant_message":
                            content = payload.get("message", "")
                            if content:
                                messages.append({"role": "assistant", "content": content})

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        console.print(f"[red]解析失败 {jsonl_file.name}: {e}[/red]")
        return None

    if not messages:
        return None

    return {
        "id": session_id or jsonl_file.stem,
        "file": str(jsonl_file),
        "messages": messages,
        "date": datetime.fromtimestamp(jsonl_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    }


def _sync_conversation_to_wiki(conv: dict, wiki_ctx: WikiContext, provider_override=None):
    """将对话同步到 wiki"""
    import asyncio
    from ..core.ingest_engine import ingest_conversation

    topic = conv.get("topic", "cc-conversations")
    conv_domain = _get_conversation_domain(wiki_ctx)
    provider = provider_override or wiki_ctx.create_provider()
    try:
        return asyncio.run(ingest_conversation(
            conversation_id=conv["id"],
            messages=conv["messages"],
            topic=topic,
            domain_path=conv_domain,
            provider=provider,
            language=wiki_ctx.language
        ))
    except Exception as e:
        console.print(f"[red]同步失败 {conv['id'][:20]}: {e}[/red]")
        return None


def _create_providers(wiki_ctx: WikiContext) -> list:
    """创建所有可用的 provider 实例，用于轮流调用"""
    from ..config import load_config
    providers = []
    cfg = load_config()
    for name, p_cfg in cfg.get("providers", {}).items():
        try:
            provider = wiki_ctx.create_provider(name)
            providers.append((name, provider))
        except Exception:
            continue
    return providers


def _collect_all_pending(wiki_ctx: WikiContext, min_messages: int = 5) -> list:
    """收集所有待处理的对话和 plan"""
    sync_record_path = Path.home() / ".wiki" / "conversation_sync.json"
    processed_files = set()
    if sync_record_path.exists():
        with open(sync_record_path, "r", encoding="utf-8") as f:
            processed_files = set(json.load(f).get("processed", []))

    all_items = []

    # 扫描 Claude Code 对话
    cc_dir = Path.home() / ".claude" / "projects"
    if cc_dir.exists():
        for jsonl_file in cc_dir.rglob("*.jsonl"):
            if str(jsonl_file) in processed_files:
                continue
            conv = _parse_conversation(jsonl_file)
            if conv and len(conv["messages"]) >= min_messages:
                conv["tool"] = "Claude Code"
                conv["topic"] = "cc-conversations"
                all_items.append(conv)

    # 扫描 CodeX 对话
    codex_dir = Path.home() / ".codex" / "sessions"
    if codex_dir.exists():
        for jsonl_file in codex_dir.rglob("*.jsonl"):
            if str(jsonl_file) in processed_files:
                continue
            conv = _parse_codex_conversation(jsonl_file)
            if conv and len(conv["messages"]) >= min_messages:
                conv["tool"] = "CodeX"
                conv["topic"] = "codex-conversations"
                all_items.append(conv)

    # 扫描 Claude Code plan 文件
    plans_dir = Path.home() / ".claude" / "plans"
    if plans_dir.exists():
        for plan_file in plans_dir.rglob("*.md"):
            if str(plan_file) in processed_files:
                continue
            try:
                content = plan_file.read_text(encoding="utf-8")
                if len(content) < 100:
                    continue
                all_items.append({
                    "id": f"plan-{plan_file.stem}",
                    "file": str(plan_file),
                    "messages": [{"role": "assistant", "content": content}],
                    "tool": "Claude Code Plan",
                    "topic": "cc-plans",
                    "date": datetime.fromtimestamp(plan_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            except Exception:
                continue

    all_items.sort(key=lambda c: len(c["messages"]), reverse=True)
    return all_items, processed_files, sync_record_path


@conversation.command()
@click.option("--hours", default=1, help="同步间隔（小时）")
@click.pass_context
def schedule(ctx, hours):
    """创建定时任务，每小时自动同步对话。"""
    import subprocess
    import sys

    wiki_exe = sys.executable.replace("python.exe", "Scripts\\wiki.exe")
    task_name = "WikiConversationSync"

    ps_cmd = f"""
$action = New-ScheduledTaskAction -Execute '{wiki_exe}' -Argument 'conversation sync --hours {hours}'
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours {hours}) -Once -At (Get-Date)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force
"""
    result = subprocess.run(
        ["powershell", "-Command", ps_cmd],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        console.print(f"[green]✓[/green] 已创建定时任务: {task_name}")
        console.print(f"  每 {hours} 小时自动同步对话到 wiki")
        console.print(f"  查看: [cyan]Get-ScheduledTask -TaskName {task_name}[/cyan]")
        console.print(f"  删除: [cyan]wiki conversation unschedule[/cyan]")
    else:
        console.print(f"[red]创建定时任务失败:[/red] {result.stderr}")
        console.print(f"\n[dim]手动运行: wiki conversation sync --hours {hours}[/dim]")


@conversation.command()
def unschedule():
    """删除定时同步任务。"""
    import subprocess
    result = subprocess.run(
        ["powershell", "-Command", "Unregister-ScheduledTask -TaskName 'WikiConversationSync' -Confirm:$false; Unregister-ScheduledTask -TaskName 'WikiNightSync' -Confirm:$false -ErrorAction SilentlyContinue"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] 已删除定时任务")
    else:
        console.print(f"[red]删除失败:[/red] {result.stderr}")


@conversation.command()
@click.option("--min-messages", default=5, help="最少消息数")
@click.option("--dry-run", is_flag=True, help="预览模式")
@click.pass_context
def night(ctx, min_messages, dry_run):
    """夜间批量处理：双 provider 轮流处理所有未导入的对话和 plan。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.data_dir:
        console.print("[red]错误: 未初始化[/red]")
        return

    # 创建所有 provider
    providers = _create_providers(wiki_ctx)
    if not providers:
        console.print("[red]错误: 没有可用的 provider[/red]")
        return

    console.print(f"[cyan]可用 Provider ({len(providers)}):[/cyan]")
    for name, _ in providers:
        console.print(f"  • {name}")

    # 收集待处理项
    all_items, processed_files, sync_record_path = _collect_all_pending(wiki_ctx, min_messages)

    if not all_items:
        console.print("[yellow]没有待处理的对话或 plan[/yellow]")
        return

    # 统计
    conv_count = sum(1 for i in all_items if not i["id"].startswith("plan-"))
    plan_count = sum(1 for i in all_items if i["id"].startswith("plan-"))
    console.print(f"[green]待处理: {conv_count} 个对话, {plan_count} 个 plan[/green]")

    if dry_run:
        from rich.table import Table
        table = Table(title="待处理项")
        table.add_column("类型", style="cyan")
        table.add_column("ID", style="white")
        table.add_column("消息数", style="yellow")
        table.add_column("时间", style="dim")

        for item in all_items[:20]:
            table.add_row(
                item["tool"],
                item["id"][:40],
                str(len(item["messages"])),
                item["date"]
            )
        console.print(table)
        if len(all_items) > 20:
            console.print(f"[dim]...还有 {len(all_items) - 20} 项[/dim]")
        return

    # 双 provider 轮流处理
    imported = []
    failed = []

    with Progress() as progress:
        task = progress.add_task("[cyan]夜间处理中...", total=len(all_items))

        for i, item in enumerate(all_items):
            # 轮流使用 provider
            provider_name, provider_instance = providers[i % len(providers)]

            try:
                result = _sync_conversation_to_wiki(item, wiki_ctx, provider_override=provider_instance)
                if result:
                    imported.append(item["file"])
                    processed_files.add(item["file"])
                else:
                    failed.append(item["id"])
            except Exception as e:
                console.print(f"\n[red]{item['id'][:20]}: {e}[/red]")
                failed.append(item["id"])

            progress.update(task, advance=1)

            # 定期保存进度
            if len(imported) % 5 == 0:
                sync_record_path.parent.mkdir(parents=True, exist_ok=True)
                with open(sync_record_path, "w", encoding="utf-8") as f:
                    json.dump({"processed": list(processed_files)}, f, ensure_ascii=False)

    # 最终保存
    sync_record_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sync_record_path, "w", encoding="utf-8") as f:
        json.dump({"processed": list(processed_files)}, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]✓[/green] 成功处理 {len(imported)} 项")
    if failed:
        console.print(f"[red]✗[/red] 失败 {len(failed)} 项")


@conversation.command()
@click.option("--time", "run_time", default="02:00", help="每天执行时间（默认 02:00）")
@click.pass_context
def night_schedule(ctx, run_time):
    """设置夜间自动处理定时任务。"""
    import subprocess
    import sys

    wiki_exe = sys.executable.replace("python.exe", "Scripts\\wiki.exe")
    task_name = "WikiNightSync"

    ps_cmd = f"""
$action = New-ScheduledTaskAction -Execute '{wiki_exe}' -Argument 'conversation night'
$trigger = New-ScheduledTaskTrigger -Daily -At '{run_time}'
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) -StartWhenAvailable
Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force
"""
    result = subprocess.run(
        ["powershell", "-Command", ps_cmd],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        console.print(f"[green]✓[/green] 已创建夜间定时任务: {task_name}")
        console.print(f"  每天 {run_time} 自动处理所有未导入的对话和 plan")
        console.print(f"  使用所有 provider 轮流处理，降低单个 provider 压力")
        console.print(f"  删除: [cyan]wiki conversation unschedule[/cyan]")
    else:
        console.print(f"[red]创建失败:[/red] {result.stderr}")
