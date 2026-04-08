from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.parsers.base import SourceParser


class CMFParser(SourceParser):
    def parse(self, fetch_result, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(fetch_result.html or "", "lxml")
        films: list[ExtractedFilm] = []
        for card in soup.select("article, .views-row, .card"):
            text = card.get_text(" ", strip=True)
            if not text:
                continue
            title = text.split("  ")[0].strip()
            if len(title) < 3:
                continue
            films.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="funded",
                    confidence_score=92,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    budget_text="Unknown",
                    notes="CMF parser extracted a project candidate from listing markup.",
                )
            )
        return films
