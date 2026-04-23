"""Filesystem operations for wiki pages."""

from pathlib import Path
from typing import Iterator


def read_page(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_page(path: Path, content: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)


def iter_wiki_pages(wiki_dir: Path) -> Iterator[Path]:
    if not wiki_dir.exists():
        return
    for md in wiki_dir.rglob("*.md"):
        yield md


def iter_raw_files(raw_dir: Path) -> Iterator[Path]:
    if not raw_dir.exists():
        return
    for f in raw_dir.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".txt", ".pdf"):
            yield f
