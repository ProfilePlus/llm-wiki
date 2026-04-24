"""MCP tools for wiki operations."""

import json
from pathlib import Path
from typing import Any

from ..core.query_engine import query_wiki_sync
from ..core.link_parser import build_link_graph, find_backlinks
from ..core.wiki_fs import read_page, iter_wiki_pages
from .cache import WikiCache


class WikiTools:
    """MCP tools for wiki operations."""

    def __init__(self, wiki_path: Path, provider, language: str = "zh"):
        """
        Initialize wiki tools.

        Args:
            wiki_path: Path to wiki/ directory
            provider: LLM provider instance
            language: Language code (zh or en)
        """
        self.wiki_path = wiki_path
        self.provider = provider
        self.language = language
        self.cache = WikiCache(default_ttl=300)

    def search_wiki(self, query: str) -> dict[str, Any]:
        """
        Search wiki and get AI-generated answer.

        Args:
            query: Search query

        Returns:
            Dict with answer, cited_pages, and page_count
        """
        cache_key = f"search:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            result = query_wiki_sync(
                question=query,
                wiki_dir=self.wiki_path,
                provider=self.provider,
                language=self.language
            )
            self.cache.set(cache_key, result, ttl=600)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_page(self, slug: str) -> dict[str, Any]:
        """
        Get wiki page content by slug.

        Args:
            slug: Page slug (filename without .md)

        Returns:
            Dict with content and metadata
        """
        cache_key = f"page:{slug}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            page_path = None
            for md in self.wiki_path.rglob(f"{slug}.md"):
                page_path = md
                break

            if not page_path:
                return {"error": f"Page not found: {slug}"}

            content = read_page(page_path)
            result = {
                "slug": slug,
                "content": content,
                "path": str(page_path.relative_to(self.wiki_path))
            }
            self.cache.set(cache_key, result)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_backlinks(self, slug: str) -> dict[str, Any]:
        """
        Get pages that link to the specified page.

        Args:
            slug: Target page slug

        Returns:
            Dict with backlinks list
        """
        cache_key = f"backlinks:{slug}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            graph = build_link_graph(self.wiki_path)
            backlinks = find_backlinks(graph, slug)
            result = {"slug": slug, "backlinks": backlinks}
            self.cache.set(cache_key, result)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        """
        Get thread details by ID.

        Args:
            thread_id: Thread identifier

        Returns:
            Dict with thread data
        """
        try:
            threads_dir = self.wiki_path.parent / "threads"
            thread_file = threads_dir / f"{thread_id}.json"

            if not thread_file.exists():
                return {"error": f"Thread not found: {thread_id}"}

            with open(thread_file, "r", encoding="utf-8") as f:
                thread_data = json.load(f)

            return thread_data
        except Exception as e:
            return {"error": str(e)}

    def get_recent_threads(self, limit: int = 10) -> dict[str, Any]:
        """
        Get recent threads sorted by update time.

        Args:
            limit: Maximum number of threads to return

        Returns:
            Dict with threads list
        """
        try:
            threads_dir = self.wiki_path.parent / "threads"
            if not threads_dir.exists():
                return {"threads": []}

            threads = []
            for thread_file in threads_dir.glob("*.json"):
                try:
                    with open(thread_file, "r", encoding="utf-8") as f:
                        thread_data = json.load(f)
                        threads.append(thread_data)
                except Exception:
                    continue

            # Sort by updated_at
            threads.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
            return {"threads": threads[:limit]}
        except Exception as e:
            return {"error": str(e)}

    def get_decisions(self, limit: int = 20) -> dict[str, Any]:
        """
        Get recent decisions from decision log.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            Dict with decisions list
        """
        try:
            decisions_file = self.wiki_path / "decisions.md"
            if not decisions_file.exists():
                return {"decisions": []}

            content = read_page(decisions_file)
            lines = content.split("\n")

            decisions = []
            current_decision = None

            for line in lines:
                if line.startswith("## "):
                    if current_decision:
                        decisions.append(current_decision)
                    current_decision = {"title": line[3:].strip(), "content": ""}
                elif current_decision:
                    current_decision["content"] += line + "\n"

            if current_decision:
                decisions.append(current_decision)

            return {"decisions": decisions[:limit]}
        except Exception as e:
            return {"error": str(e)}
