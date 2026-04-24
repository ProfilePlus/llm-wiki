"""wiki thread - Thread management commands."""

import click
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..context import WikiContext

console = Console()


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
@click.pass_context
def show(ctx, thread_id):
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

    console.print(f"\n[bold cyan]{thread_data['title']}[/bold cyan]")
    console.print(f"ID: {thread_data['id']}")
    console.print(f"Status: {thread_data['status']}")
    console.print(f"Priority: {thread_data['priority']}")
    if thread_data.get('tags'):
        console.print(f"Tags: {', '.join(thread_data['tags'])}")
    console.print(f"Created: {thread_data['created_at']}")
    console.print(f"Updated: {thread_data['updated_at']}")

    if thread_data.get('description'):
        console.print(f"\n{thread_data['description']}")

    if thread_data.get('dependencies'):
        console.print(f"\nDependencies: {', '.join(thread_data['dependencies'])}")

    if thread_data.get('messages'):
        console.print(f"\nMessages: {len(thread_data['messages'])}")


@thread.command()
@click.pass_context
def list(ctx):
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
                threads.append(thread_data)
        except Exception:
            continue

    if not threads:
        console.print("[dim]No threads found[/dim]")
        return

    # Sort by updated_at
    threads.sort(key=lambda t: t.get("updated_at", ""), reverse=True)

    table = Table(title="Threads")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Priority", style="magenta")
    table.add_column("Updated", style="dim")

    for t in threads:
        table.add_row(
            t["id"],
            t["title"],
            t["status"],
            t["priority"],
            t["updated_at"][:10]
        )

    console.print(table)


@thread.command()
@click.argument("thread_id")
@click.option("--status", type=click.Choice(["open", "in_progress", "closed"]))
@click.option("--priority", type=click.Choice(["low", "medium", "high"]))
@click.pass_context
def update(ctx, thread_id, status, priority):
    """Update thread status or priority."""
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

    if status:
        thread_data["status"] = status
    if priority:
        thread_data["priority"] = priority

    thread_data["updated_at"] = datetime.now().isoformat()

    with open(thread_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, ensure_ascii=False, indent=2)

    console.print(f"[green]✓[/green] Thread updated: {thread_id}")


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
