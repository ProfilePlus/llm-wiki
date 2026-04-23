"""Lint engine: health checks and LLM suggestions."""

import asyncio
import json
from pathlib import Path

from .provider_base import LLMProvider
from .prompts import LINT_SYSTEM
from .link_parser import build_link_graph, find_orphans, find_broken
from .page_types import type_counts
from .wiki_fs import iter_wiki_pages


async def lint_wiki(wiki_dir: Path, provider: LLMProvider) -> dict:
    """
    Run health checks on the wiki.

    Args:
        wiki_dir: Path to wiki/ directory
        provider: LLM provider instance

    Returns:
        Dict with structural issues and LLM suggestions
    """
    if not wiki_dir.exists():
        return {"error": "Wiki directory does not exist"}

    # 1. Structural checks
    structural_issues = []

    # Check index.md and log.md
    if not (wiki_dir / "index.md").exists():
        structural_issues.append({
            "severity": "high",
            "type": "structural",
            "description": "缺少 index.md",
            "suggestion": "运行 wiki index 重建索引"
        })

    if not (wiki_dir / "log.md").exists():
        structural_issues.append({
            "severity": "medium",
            "type": "structural",
            "description": "缺少 log.md",
            "suggestion": "创建 log.md 记录操作历史"
        })

    # Link analysis
    graph = build_link_graph(wiki_dir)
    existing = set(graph.keys())
    orphan_list = find_orphans(graph)
    broken_list = find_broken(graph, existing)

    for orphan in orphan_list:
        structural_issues.append({
            "severity": "low",
            "type": "orphan",
            "page": orphan,
            "description": f"孤儿页：{orphan} 没有入链",
            "suggestion": "考虑从其他页面链接到此页，或删除"
        })

    for src, target in broken_list:
        structural_issues.append({
            "severity": "medium",
            "type": "broken_link",
            "page": src,
            "description": f"断链：{src} 链接到不存在的 {target}",
            "suggestion": f"创建 {target} 页面或修复链接"
        })

    # 2. LLM semantic check
    # Build wiki summary for LLM
    counts = type_counts(wiki_dir)
    page_list = []
    for p in iter_wiki_pages(wiki_dir):
        if p.name not in ("index.md", "log.md"):
            page_list.append(p.stem)

    wiki_summary = f"""
## Wiki 结构

- 总页面数: {len(page_list)}
- 页面类型分布: {json.dumps(counts, ensure_ascii=False)}
- 孤儿页: {len(orphan_list)}
- 断链: {len(broken_list)}

## 页面列表

{chr(10).join(f"- {slug}" for slug in sorted(page_list)[:50])}
{"..." if len(page_list) > 50 else ""}

## 链接图样本

{json.dumps({k: v for k, v in list(graph.items())[:10]}, ensure_ascii=False, indent=2)}
"""

    user_message = f"""
{wiki_summary}

请审查这个 wiki 的健康度，给出改进建议。
"""

    response = await provider.complete(
        system=LINT_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=4000,
    )

    # Parse LLM response
    try:
        json_str = response.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])
        llm_result = json.loads(json_str)
    except json.JSONDecodeError:
        llm_result = {"issues": [], "suggested_pages": [], "summary": "LLM 响应解析失败"}

    # Combine structural and LLM issues
    all_issues = structural_issues + llm_result.get("issues", [])

    return {
        "issues": all_issues,
        "suggested_pages": llm_result.get("suggested_pages", []),
        "summary": llm_result.get("summary", ""),
        "stats": {
            "total_pages": len(page_list),
            "orphans": len(orphan_list),
            "broken_links": len(broken_list),
            "type_counts": counts,
        }
    }


def lint_wiki_sync(wiki_dir: Path, provider: LLMProvider) -> dict:
    """Synchronous wrapper for lint_wiki."""
    return asyncio.run(lint_wiki(wiki_dir, provider))
