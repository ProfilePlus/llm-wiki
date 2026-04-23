"""Parse [[wikilinks]] and build link graph."""

import re
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_links(content: str) -> list[str]:
    return WIKILINK_RE.findall(content)


def slug_from_path(path: Path, wiki_dir: Path) -> str:
    return path.stem


def resolve_slug(slug: str, wiki_dir: Path) -> Path | None:
    if ":" in slug:
        _, slug = slug.split(":", 1)
    for md in wiki_dir.rglob(f"{slug}.md"):
        return md
    return None


def build_link_graph(wiki_dir: Path) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    if not wiki_dir.exists():
        return graph
    for md in wiki_dir.rglob("*.md"):
        slug = md.stem
        content = md.read_text(encoding="utf-8")
        graph[slug] = extract_links(content)
    return graph


def find_backlinks(graph: dict[str, list[str]], target: str) -> list[str]:
    return [src for src, links in graph.items() if target in links]


def find_orphans(graph: dict[str, list[str]]) -> list[str]:
    all_targets = {t for links in graph.values() for t in links}
    skip = {"index", "log"}
    return [src for src in graph if src not in all_targets and src not in skip]


def find_broken(graph: dict[str, list[str]], existing_slugs: set[str]) -> list[tuple[str, str]]:
    broken = []
    for src, links in graph.items():
        for link in links:
            clean = link.split(":")[-1] if ":" in link else link
            if clean not in existing_slugs:
                broken.append((src, link))
    return broken
