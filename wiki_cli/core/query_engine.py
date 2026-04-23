"""Query engine: question -> context -> LLM -> answer."""

import asyncio
from pathlib import Path

from .provider_base import LLMProvider
from .prompts import QUERY_SYSTEM
from .wiki_fs import iter_wiki_pages, read_page


async def query_wiki(question: str, wiki_dir: Path, provider: LLMProvider) -> dict:
    """
    Query the wiki using the LLM.

    Args:
        question: User's question
        wiki_dir: Path to wiki/ directory
        provider: LLM provider instance

    Returns:
        Dict with answer and cited pages
    """
    if not wiki_dir.exists():
        return {"error": "Wiki directory does not exist"}

    # Simple retrieval: keyword match + slug match + index
    question_lower = question.lower()
    relevant_pages = []

    for p in iter_wiki_pages(wiki_dir):
        content = read_page(p)
        slug = p.stem.lower()
        score = 0

        # Slug match (high priority)
        for word in question_lower.split():
            if len(word) > 2 and word in slug:
                score += 50

        # Content keyword scoring
        for word in question_lower.split():
            if len(word) > 2 and word in content.lower():
                score += content.lower().count(word)

        # Always include index
        if p.name == "index.md":
            score = max(score, 1)

        if score > 0:
            relevant_pages.append((score, p, content))

    # Sort by score, keep top 10
    relevant_pages.sort(key=lambda x: x[0], reverse=True)
    top_pages = relevant_pages[:10]

    if not top_pages:
        return {"answer": "wiki 中暂无相关内容。", "cited_pages": []}

    # Build context
    context_parts = []
    cited_slugs = []
    for score, p, content in top_pages:
        slug = p.stem
        cited_slugs.append(slug)
        context_parts.append(f"## 页面: [[{slug}]]\n\n{content}\n")

    context = "\n\n---\n\n".join(context_parts)

    user_message = f"""
## Wiki 上下文

{context}

## 用户问题

{question}

请基于以上 wiki 页面回答。只使用这些页面中的信息。
"""

    answer = await provider.complete(
        system=QUERY_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=4000,
    )

    return {
        "answer": answer,
        "cited_pages": cited_slugs,
        "page_count": len(top_pages),
    }


def query_wiki_sync(question: str, wiki_dir: Path, provider: LLMProvider) -> dict:
    """Synchronous wrapper for query_wiki."""
    return asyncio.run(query_wiki(question, wiki_dir, provider))
