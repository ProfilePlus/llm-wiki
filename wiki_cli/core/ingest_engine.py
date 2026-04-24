"""Ingest engine: source file -> raw/ -> LLM -> wiki/."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from .provider_base import LLMProvider
from .prompts import get_ingest_prompt
from .wiki_fs import read_page, write_page, append_page


async def ingest_file(
    source_path: Path,
    topic: str,
    domain_path: Path,
    provider: LLMProvider,
    language: str = "zh",
) -> dict:
    """
    Ingest a source file into the wiki.

    Args:
        source_path: Path to source file
        topic: Topic name (subdirectory)
        domain_path: Domain root path
        provider: LLM provider instance

    Returns:
        Result dict with created/updated pages
    """
    # 1. Copy to raw/
    raw_dir = domain_path / "raw" / topic
    raw_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = source_path.stem
    raw_filename = f"{date_str}-{slug}.md"
    raw_path = raw_dir / raw_filename

    # Read source content
    if source_path.suffix == ".md":
        content = source_path.read_text(encoding="utf-8")
    elif source_path.suffix == ".txt":
        content = source_path.read_text(encoding="utf-8")
    else:
        return {"error": f"Unsupported file type: {source_path.suffix}"}

    # Copy to raw/
    raw_path.write_text(content, encoding="utf-8")

    # 2. Read existing wiki context
    wiki_dir = domain_path / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    index_path = wiki_dir / "index.md"
    index_content = ""
    if index_path.exists():
        index_content = read_page(index_path)

    # Build context: existing pages in this topic
    topic_dir = wiki_dir / topic
    existing_pages = []
    if topic_dir.exists():
        for p in topic_dir.glob("*.md"):
            existing_pages.append(f"- {p.stem}: {read_page(p)[:200]}...")

    context_summary = f"""
## 当前 Wiki 状态

### Index 摘要
{index_content[:500] if index_content else "(空)"}

### {topic} 领域已有页面
{chr(10).join(existing_pages) if existing_pages else "(无)"}
"""

    # 3. Call LLM
    user_message = f"""
## 源文档

**文件名**: {source_path.name}
**Topic**: {topic}

**内容**:
{content}

{context_summary}

请编译这个源文档到 wiki。
"""

    response = await provider.complete(
        system=get_ingest_prompt(language),
        messages=[{"role": "user", "content": user_message}],
        max_tokens=8000,
    )

    # 4. Parse LLM response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse LLM response: {e}", "raw_response": response}

    # 5. Write pages
    created = []
    updated = []

    for page in result.get("pages_to_create", []):
        page_type = page["type"]
        page_slug = page["slug"]
        page_topic = page.get("topic", topic)
        page_content = page["content"]

        # Construct filename with type prefix
        filename = f"{page_type}-{page_slug}.md"
        page_path = wiki_dir / page_topic / filename
        write_page(page_path, page_content)
        created.append(str(page_path.relative_to(domain_path)))

    for update in result.get("pages_to_update", []):
        update_slug = update["slug"]
        append_content = update.get("append_content", "")

        # Find the page
        matches = list(wiki_dir.rglob(f"{update_slug}.md"))
        if matches:
            page_path = matches[0]
            append_page(page_path, f"\n\n{append_content}")
            updated.append(str(page_path.relative_to(domain_path)))

    # 6. Update log.md
    log_path = wiki_dir / "log.md"
    log_entry = f"""
## {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - ingest

- **Source**: {raw_path.relative_to(domain_path)}
- **Topic**: {topic}
- **Created**: {", ".join(created) if created else "(无)"}
- **Updated**: {", ".join(updated) if updated else "(无)"}
- **Summary**: {result.get("log_entry", "")}
"""
    append_page(log_path, log_entry)

    return {
        "status": "ok",
        "raw_path": str(raw_path),
        "created": created,
        "updated": updated,
        "log_entry": result.get("log_entry", ""),
    }


def ingest_file_sync(source_path: Path, topic: str, domain_path: Path, provider: LLMProvider, language: str = "zh") -> dict:
    """Synchronous wrapper for ingest_file."""
    return asyncio.run(ingest_file(source_path, topic, domain_path, provider, language))


async def ingest_conversation(
    conversation_id: str,
    messages: list,
    topic: str,
    domain_path: Path,
    provider: LLMProvider,
    language: str = "zh",
) -> dict:
    """将对话内容写入 wiki，复用 ingest_file 逻辑。"""
    # 格式化对话为 markdown
    lines = [f"# Conversation: {conversation_id}", f"", f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for msg in messages:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = str(msg.get("content", ""))[:2000]  # 截断超长消息
        lines.append(f"**{role}**: {content}")
        lines.append("")
    content = "\n".join(lines)

    # 写入临时文件，复用 ingest_file
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)

    try:
        result = await ingest_file(tmp_path, topic, domain_path, provider, language)
    finally:
        os.unlink(tmp_path)

    return result
