from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.utils.quality import is_probable_project_title


class PlaybackParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        for article in soup.select("article"):
            heading = article.select_one("h2, h3")
            if not heading:
                continue
            title = heading.get_text(" ", strip=True)
            if not is_probable_project_title(title):
                continue
            items.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="unknown",
                    confidence_score=70,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    budget_text="Unknown",
                    notes="Trade candidate requiring downstream filtering.",
                )
            )
        return items
