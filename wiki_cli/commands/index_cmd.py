"""wiki index - Rebuild index.md."""

import click
from rich.console import Console

from ..context import WikiContext
from ..core.wiki_fs import iter_wiki_pages
from ..core.page_types import detect_type
from ..output import is_machine_mode, output_json

console = Console()


@click.command("index")
@click.pass_context
def index_cmd(ctx):
    """重建 index.md。"""
    wiki_ctx: WikiContext = ctx.obj
    if not wiki_ctx.wiki_path:
        console.print("[yellow]请先设置活跃领域[/yellow]")
        return

    # Group pages by topic and type
    topics: dict[str, dict[str, list[str]]] = {}
    for p in iter_wiki_pages(wiki_ctx.wiki_path):
        if p.name in ("index.md", "log.md"):
            continue
        rel = p.relative_to(wiki_ctx.wiki_path)
        topic = rel.parent.as_posix() if rel.parent.as_posix() != "." else "general"
        pt = detect_type(p) or "other"
        topics.setdefault(topic, {}).setdefault(pt, []).append(p.stem)

    # Build index content
    domain = wiki_ctx.active_domain or "wiki"
    lines = [f"# {domain} Wiki Index\n", "> 此文件由 `wiki index` 自动生成。\n"]

    for topic in sorted(topics):
        lines.append(f"\n## {topic}\n")
        for pt in sorted(topics[topic]):
            lines.append(f"\n### {pt}\n")
            for slug in sorted(topics[topic][pt]):
                lines.append(f"- [[{slug}]]")

    content = "\n".join(lines) + "\n"
    index_path = wiki_ctx.wiki_path / "index.md"
    index_path.write_text(content, encoding="utf-8")

    page_count = sum(len(slugs) for types in topics.values() for slugs in types.values())

    if is_machine_mode():
        output_json({"status": "ok", "topics": len(topics), "pages": page_count})
    else:
        console.print(f"[green]✓[/green] index.md 已重建: {len(topics)} 个 topic, {page_count} 个页面")
