from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.parsers.sources.common import extract_title_from_container, has_project_signal


class NFBNewsParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        seen_titles: set[str] = set()
        for article in soup.select("article, li, .news, .gc-nws"):
            title = extract_title_from_container(article, ("h1", "h2", "h3", "a"))
            if not title:
                continue
            context_text = article.get_text(" ", strip=True)
            if not has_project_signal(context_text):
                continue
            normalized = title.lower()
            if normalized in seen_titles:
                continue
            seen_titles.add(normalized)
            items.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="production",
                    confidence_score=82,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    budget_text="Unknown",
                    notes="Extracted from NFB news item with explicit production signal.",
                )
            )
        return items
