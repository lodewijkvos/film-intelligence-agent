from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.parsers.base import SourceParser


class PlaybackParser(SourceParser):
    def parse(self, fetch_result, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(fetch_result.html or "", "lxml")
        items: list[ExtractedFilm] = []
        for article in soup.select("article"):
            heading = article.select_one("h2, h3")
            if not heading:
                continue
            title = heading.get_text(" ", strip=True)
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
                    notes="Playback parser extracted an article candidate for downstream filtering.",
                )
            )
        return items
