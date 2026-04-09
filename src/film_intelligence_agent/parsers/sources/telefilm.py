from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.utils.quality import is_probable_project_title


class TelefilmParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        films: list[ExtractedFilm] = []
        for heading in soup.select("h2, h3"):
            title = heading.get_text(" ", strip=True)
            if not is_probable_project_title(title):
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
                    notes="Extracted from Telefilm heading structure.",
                )
            )
        return films
