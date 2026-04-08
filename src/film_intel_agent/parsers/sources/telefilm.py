from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.parsers.base import SourceParser


class TelefilmDirectoryParser(SourceParser):
    def parse(self, fetch_result, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(fetch_result.html or "", "lxml")
        films: list[ExtractedFilm] = []
        for heading in soup.select("h2, h3"):
            title = heading.get_text(" ", strip=True)
            if not title or len(title) < 3:
                continue
            films.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="funded",
                    confidence_score=95,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    budget_text="Unknown",
                    notes="Telefilm parser extracted title from heading structure.",
                )
            )
        return films
