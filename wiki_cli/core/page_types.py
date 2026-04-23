"""Page type detection from filename prefix."""

from pathlib import Path
from ..constants import PAGE_TYPES


def detect_type(path: Path) -> str | None:
    stem = path.stem
    for pt in PAGE_TYPES:
        if stem.startswith(f"{pt}-"):
            return pt
    return None


def type_counts(wiki_dir: Path) -> dict[str, int]:
    counts = {pt: 0 for pt in PAGE_TYPES}
    counts["other"] = 0
    if not wiki_dir.exists():
        return counts
    for md in wiki_dir.rglob("*.md"):
        if md.name in ("index.md", "log.md"):
            continue
        pt = detect_type(md)
        if pt:
            counts[pt] += 1
        else:
            counts["other"] += 1
    return counts
