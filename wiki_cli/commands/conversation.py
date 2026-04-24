"""wiki conversation - Sync Claude Code conversations to wiki."""

import click
import json
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress

from ..context import WikiContext

console = Console()


@click.group()
def conversation():
    """Sync Claude Code conversations to wiki."""
    pass


@conversation.command()
@click.option("--hours", default=1, help="Sync conversations from last N hours")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without actually syncing")
@click.pass_context
def sync(ctx, hours, dry_run):
    """Sync recent Claude Code conversations to wiki."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]Error: No active domain[/red]")
        return

    # Claude Code 对话历史路径
    claude_projects_dir = Path.home() / ".claude" / "projects"
    if not claude_projects_dir.exists():
        console.print("[red]Error: Claude Code projects directory not found[/red]")
        return

    # 查找最近的对话文件
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_conversations = []

    console.print(f"[cyan]Scanning conversations from last {hours} hour(s)...[/cyan]")

    for jsonl_file in claude_projects_dir.rglob("*.jsonl"):
        # 跳过非对话文件
        if jsonl_file.stat().st_mtime < cutoff_time.timestamp():
            continue

        # 解析对话
        conversation = _parse_conversation(jsonl_file)
        if conversation and conversation["messages"]:
            recent_conversations.append(conversation)

    if not recent_conversations:
        console.print("[yellow]No recent conversations found[/yellow]")
        return

    console.print(f"[green]Found {len(recent_conversations)} conversation(s)[/green]")

    if dry_run:
        for conv in recent_conversations:
            console.print(f"\n[bold]{conv['id']}[/bold]")
            console.print(f"  Messages: {len(conv['messages'])}")
            console.print(f"  Date: {conv['date']}")
        console.print("\n[dim]Run without --dry-run to sync[/dim]")
        return

    # 同步到 wiki
    with Progress() as progress:
        task = progress.add_task("[cyan]Syncing...", total=len(recent_conversations))

        for conv in recent_conversations:
            _sync_conversation_to_wiki(conv, wiki_ctx)
            progress.update(task, advance=1)

    console.print(f"[green]✓[/green] Synced {len(recent_conversations)} conversation(s)")


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
                            # 提取文本内容
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
        console.print(f"[red]Error parsing {jsonl_file.name}: {e}[/red]")
        return None

    if not messages:
        return None

    return {
        "id": session_id or jsonl_file.stem,
        "file": str(jsonl_file),
        "messages": messages,
        "date": datetime.fromtimestamp(jsonl_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    }


@conversation.command()
@click.option("--hours", default=1, help="Sync interval in hours")
@click.pass_context
def schedule(ctx, hours):
    """Setup hourly auto-sync via Windows Task Scheduler."""
    import subprocess
    import sys

    wiki_exe = sys.executable.replace("python.exe", "Scripts\\wiki.exe")
    task_name = "WikiConversationSync"
    cmd = f'"{wiki_exe}" conversation sync --hours {hours}'

    # 创建 Windows 计划任务
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
        console.print(f"  查看任务: [cyan]Get-ScheduledTask -TaskName {task_name}[/cyan]")
        console.print(f"  删除任务: [cyan]Unregister-ScheduledTask -TaskName {task_name}[/cyan]")
    else:
        console.print(f"[red]创建定时任务失败:[/red] {result.stderr}")
        console.print(f"\n[dim]手动运行: wiki conversation sync --hours {hours}[/dim]")


@conversation.command()
def unschedule():
    """Remove auto-sync scheduled task."""
    import subprocess
    result = subprocess.run(
        ["powershell", "-Command", "Unregister-ScheduledTask -TaskName 'WikiConversationSync' -Confirm:$false"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] 已删除定时任务")
    else:
        console.print(f"[red]删除失败:[/red] {result.stderr}")
    import asyncio
    from ..core.ingest_engine import ingest_conversation

    try:
        result = asyncio.run(ingest_conversation(
            conversation_id=conversation["id"],
            messages=conversation["messages"],
            topic="conversations",
            domain_path=wiki_ctx.domain_path,
            provider=wiki_ctx.create_provider(),
            language=wiki_ctx.language
        ))
        return result
    except Exception as e:
        console.print(f"[red]Error syncing {conversation['id']}: {e}[/red]")
        return None
