"""wiki conversation - 同步 Claude Code 对话到 wiki。"""

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
    """对话同步命令。"""
    pass


@conversation.command()
@click.option("--hours", default=1, help="同步最近 N 小时的对话")
@click.option("--dry-run", is_flag=True, help="预览模式，不实际同步")
@click.pass_context
def sync(ctx, hours, dry_run):
    """同步最近的 Claude Code 对话到 wiki。"""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.active_domain:
        console.print("[red]错误: 未设置活跃领域[/red]")
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


def _sync_conversation_to_wiki(conv: dict, wiki_ctx: WikiContext):
    """将对话同步到 wiki"""
    import asyncio
    from ..core.ingest_engine import ingest_conversation

    try:
        return asyncio.run(ingest_conversation(
            conversation_id=conv["id"],
            messages=conv["messages"],
            topic="conversations",
            domain_path=wiki_ctx.domain_path,
            provider=wiki_ctx.create_provider(),
            language=wiki_ctx.language
        ))
    except Exception as e:
        console.print(f"[red]同步失败 {conv['id']}: {e}[/red]")
        return None


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
        ["powershell", "-Command", "Unregister-ScheduledTask -TaskName 'WikiConversationSync' -Confirm:$false"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] 已删除定时任务")
    else:
        console.print(f"[red]删除失败:[/red] {result.stderr}")
