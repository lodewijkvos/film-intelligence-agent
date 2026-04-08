from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser


class CreativeBCParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        for row in soup.select("tr, li, article"):
            title = row.get_text(" ", strip=True)
            if len(title) < 3:
                continue
            items.append(
                ExtractedFilm(
                    title=title.split(" - ")[0],
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="production",
                    confidence_score=88,
                    date_detected=datetime.utcnow(),
                    country="Canada",
                    region="Canada",
                    province_or_state="British Columbia",
                    budget_text="Unknown",
                    notes="Extracted from Creative BC list structure.",
                )
            )
        return items
