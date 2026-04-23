"""Dual output mode: Rich for humans, JSON for Claude Code."""

import json
import os
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def is_machine_mode() -> bool:
    """Detect if output should be JSON for machine consumption."""
    return not sys.stdout.isatty() or os.environ.get("WIKI_JSON") == "1"


def output_json(data: Any) -> None:
    """Output data as JSON."""
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def output(data: Any, *, json_mode: bool | None = None) -> None:
    """Output data as Rich or JSON depending on mode."""
    if json_mode is None:
        json_mode = is_machine_mode()

    if json_mode:
        output_json(data)
    else:
        if isinstance(data, dict):
            # Generic dict display as table
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")
            for key, value in data.items():
                table.add_row(str(key), str(value))
            console.print(table)
        else:
            console.print(data)


def show_panel(title: str, content: str) -> None:
    """Show a rich panel."""
    console.print(Panel(content, title=title, border_style="blue"))
