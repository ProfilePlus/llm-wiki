"""wiki thread - Thread management commands."""

import click
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from ..context import WikiContext

console = Console()

PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_ICONS = {"open": "⬜", "in_progress": "🟡", "closed": "✅"}


@click.group()
def thread():
    """Thread management commands."""
    pass


@thread.command()
@click.argument("thread_id")
@click.option("--title", required=True, help="Thread title")
@click.option("--description", help="Thread description")
@click.option("--priority", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--tags", help="Comma-separated tags")
@click.pass_context
def create(ctx, thread_id, title, description, priority, tags):
    """Create a new thread."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    threads_dir.mkdir(exist_ok=True)

    thread_file = threads_dir / f"{thread_id}.json"
    if thread_file.exists():
        console.print(f"[red]Error: Thread {thread_id} already exists[/red]")
        return

    thread_data = {
        "id": thread_id,
        "title": title,
        "description": description or "",
        "priority": priority,
        "tags": [t.strip() for t in tags.split(",")] if tags else [],
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "dependencies": [],
        "messages": []
    }

    with open(thread_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, ensure_ascii=False, indent=2)

    console.print(f"[green]✓[/green] Thread created: {thread_id}")


@thread.command()
@click.argument("thread_id")
@click.option("--show-deps", is_flag=True, help="Show dependency tree")
@click.pass_context
def show(ctx, thread_id, show_deps):
    """Show thread details."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    thread_file = threads_dir / f"{thread_id}.json"

    if not thread_file.exists():
        console.print(f"[red]Error: Thread {thread_id} not found[/red]")
        return

    with open(thread_file, "r", encoding="utf-8") as f:
        thread_data = json.load(f)

    priority_icon = PRIORITY_ICONS.get(thread_data['priority'], "")
    status_icon = STATUS_ICONS.get(thread_data['status'], "")

    console.print(f"\n[bold cyan]{thread_data['title']}[/bold cyan]")
    console.print(f"ID: {thread_data['id']}")
    console.print(f"Status: {status_icon} {thread_data['status']}")
    console.print(f"Priority: {priority_icon} {thread_data['priority']}")
    if thread_data.get('tags'):
        tags_str = " ".join([f"#{tag}" for tag in thread_data['tags']])
        console.print(f"Tags: {tags_str}")
    console.print(f"Created: {thread_data['created_at']}")
    console.print(f"Updated: {thread_data['updated_at']}")

    if thread_data.get('description'):
        console.print(f"\n{thread_data['description']}")

    if thread_data.get('dependencies'):
        console.print(f"\n[bold]Dependencies:[/bold]")
        if show_deps:
            tree = _build_dependency_tree(threads_dir, thread_id, set())
            console.print(tree)
        else:
            for dep_id in thread_data['dependencies']:
                console.print(f"  • {dep_id}")
            console.print("[dim](Use --show-deps to see full tree)[/dim]")

    if thread_data.get('messages'):
        console.print(f"\n[bold]Messages ({len(thread_data['messages'])}):[/bold]")
        for msg in thread_data['messages'][-5:]:  # 只显示最近 5 条
            tool = msg.get('tool', 'unknown')
            action = msg.get('action', '')
            timestamp = msg['timestamp'][:16]
            console.print(f"  [{timestamp}] [{tool}] {action}: {msg['content'][:60]}...")


def _build_dependency_tree(threads_dir: Path, thread_id: str, visited: set) -> Tree:
    """递归构建依赖树"""
    if thread_id in visited:
        return Tree(f"[dim]{thread_id} (循环依赖)[/dim]")

    visited.add(thread_id)
    thread_file = threads_dir / f"{thread_id}.json"

    if not thread_file.exists():
        return Tree(f"[red]{thread_id} (不存在)[/red]")

    with open(thread_file, "r", encoding="utf-8") as f:
        thread_data = json.load(f)

    priority_icon = PRIORITY_ICONS.get(thread_data['priority'], "")
    status_icon = STATUS_ICONS.get(thread_data['status'], "")
    tree = Tree(f"{status_icon} {priority_icon} {thread_id}: {thread_data['title']}")

    for dep_id in thread_data.get('dependencies', []):
        subtree = _build_dependency_tree(threads_dir, dep_id, visited.copy())
        tree.add(subtree)

    return tree


@thread.command()
@click.option("--status", type=click.Choice(["open", "in_progress", "closed"]), help="Filter by status")
@click.option("--priority", type=click.Choice(["low", "medium", "high"]), help="Filter by priority")
@click.option("--tag", help="Filter by tag")
@click.pass_context
def list(ctx, status, priority, tag):
    """List all threads."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    if not threads_dir.exists():
        console.print("[dim]No threads found[/dim]")
        return

    threads = []
    for thread_file in threads_dir.glob("*.json"):
        try:
            with open(thread_file, "r", encoding="utf-8") as f:
                thread_data = json.load(f)
                # 过滤
                if status and thread_data.get("status") != status:
                    continue
                if priority and thread_data.get("priority") != priority:
                    continue
                if tag and tag not in thread_data.get("tags", []):
                    continue
                threads.append(thread_data)
        except Exception:
            continue

    if not threads:
        console.print("[dim]No threads found[/dim]")
        return

    # Sort by priority (high > medium > low) then updated_at
    priority_order = {"high": 0, "medium": 1, "low": 2}
    threads.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t.get("updated_at", "")), reverse=True)

    table = Table(title="Threads")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Priority", style="magenta")
    table.add_column("Tags", style="dim")
    table.add_column("Updated", style="dim")

    for t in threads:
        status_icon = STATUS_ICONS.get(t["status"], "")
        priority_icon = PRIORITY_ICONS.get(t["priority"], "")
        tags_str = " ".join([f"#{tag}" for tag in t.get("tags", [])])
        table.add_row(
            t["id"],
            t["title"],
            f"{status_icon} {t['status']}",
            f"{priority_icon} {t['priority']}",
            tags_str,
            t["updated_at"][:10]
        )

    console.print(table)


@thread.command()
@click.argument("thread_id")
@click.option("--status", type=click.Choice(["open", "in_progress", "closed"]))
@click.option("--priority", type=click.Choice(["low", "medium", "high"]))
@click.option("--add-tags", help="Add tags (comma-separated)")
@click.option("--remove-tags", help="Remove tags (comma-separated)")
@click.pass_context
def update(ctx, thread_id, status, priority, add_tags, remove_tags):
    """Update thread status, priority, or tags."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    thread_file = threads_dir / f"{thread_id}.json"

    if not thread_file.exists():
        console.print(f"[red]Error: Thread {thread_id} not found[/red]")
        return

    with open(thread_file, "r", encoding="utf-8") as f:
        thread_data = json.load(f)

    changes = []
    if status:
        thread_data["status"] = status
        changes.append(f"status → {status}")
    if priority:
        thread_data["priority"] = priority
        changes.append(f"priority → {priority}")
    if add_tags:
        new_tags = [t.strip() for t in add_tags.split(",")]
        existing = set(thread_data.get("tags", []))
        for tag in new_tags:
            existing.add(tag)
        thread_data["tags"] = sorted(existing)
        changes.append(f"added tags: {', '.join(new_tags)}")
    if remove_tags:
        rm_tags = [t.strip() for t in remove_tags.split(",")]
        existing = set(thread_data.get("tags", []))
        for tag in rm_tags:
            existing.discard(tag)
        thread_data["tags"] = sorted(existing)
        changes.append(f"removed tags: {', '.join(rm_tags)}")

    if not changes:
        console.print("[yellow]No changes specified[/yellow]")
        return

    thread_data["updated_at"] = datetime.now().isoformat()

    with open(thread_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, ensure_ascii=False, indent=2)

    console.print(f"[green]✓[/green] Thread updated: {thread_id}")
    for change in changes:
        console.print(f"  • {change}")


@thread.command()
@click.argument("thread_id")
@click.argument("message")
@click.option("--tool", type=click.Choice(["cc", "codex", "gemini"]), help="Tool that created this message")
@click.option("--action", help="Action type (e.g., diagnosis, fix, optimization)")
@click.pass_context
def add_message(ctx, thread_id, message, tool, action):
    """Add a message to thread."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    thread_file = threads_dir / f"{thread_id}.json"

    if not thread_file.exists():
        console.print(f"[red]Error: Thread {thread_id} not found[/red]")
        return

    with open(thread_file, "r", encoding="utf-8") as f:
        thread_data = json.load(f)

    msg_data = {
        "content": message,
        "timestamp": datetime.now().isoformat()
    }
    if tool:
        msg_data["tool"] = tool
    if action:
        msg_data["action"] = action

    thread_data["messages"].append(msg_data)
    thread_data["updated_at"] = datetime.now().isoformat()

    with open(thread_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, ensure_ascii=False, indent=2)

    console.print(f"[green]✓[/green] Message added to thread: {thread_id}")


@thread.command()
@click.argument("thread_id")
@click.argument("dependency_id")
@click.pass_context
def add_dependency(ctx, thread_id, dependency_id):
    """Add a dependency to thread."""
    wiki_ctx: WikiContext = ctx.obj

    if not wiki_ctx.domain_path:
        console.print("[red]Error: No active domain[/red]")
        return

    threads_dir = wiki_ctx.domain_path / "threads"
    thread_file = threads_dir / f"{thread_id}.json"

    if not thread_file.exists():
        console.print(f"[red]Error: Thread {thread_id} not found[/red]")
        return

    with open(thread_file, "r", encoding="utf-8") as f:
        thread_data = json.load(f)

    if dependency_id not in thread_data["dependencies"]:
        thread_data["dependencies"].append(dependency_id)
        thread_data["updated_at"] = datetime.now().isoformat()

        with open(thread_file, "w", encoding="utf-8") as f:
            json.dump(thread_data, f, ensure_ascii=False, indent=2)

        console.print(f"[green]✓[/green] Dependency added: {dependency_id}")
    else:
        console.print(f"[yellow]Dependency already exists[/yellow]")
