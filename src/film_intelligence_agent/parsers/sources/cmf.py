from __future__ import annotations

from datetime import datetime
import re

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.utils.quality import is_probable_project_title

KNOWN_FIELD_LABELS = {
    "Fiscal Year",
    "Content Type",
    "Commitment",
    "Envelope/Broadcaster",
    "Activity",
    "Genre",
    "Delivery Method",
    "Region",
    "Program",
    "Status",
    "Language",
    "Selection Round",
    "Funding Stream",
}

ALLOWED_CONTENT_TYPE_FRAGMENTS = (
    "feature",
    "documentary",
    "series",
    "television",
    "tv",
    "episodic",
    "drama",
    "comedy",
    "animation",
)

ALLOWED_PROGRAM_FRAGMENTS = (
    "linear",
    "regional production funding",
    "indigenous production program",
    "pov program",
    "official language minority communities",
    "program for black and racialized communities",
    "broadcaster envelope",
    "distributor envelope",
)

DISALLOWED_CONTENT_TYPE_FRAGMENTS = (
    "game",
    "interactive",
    "immersive",
    "application",
)


class CMFParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        text = soup.get_text("\n", strip=True)
        if "Search for funded projects" not in text or "Export Results" not in text:
            return items
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        try:
            start_index = next(i for i, line in enumerate(lines) if "Export Results" in line) + 1
        except StopIteration:
            return items
        seen_titles: set[str] = set()
        i = start_index
        while i < len(lines):
            raw_heading = lines[i]
            if raw_heading in KNOWN_FIELD_LABELS:
                i += 1
                continue
            if i + 1 >= len(lines) or lines[i + 1] != "Fiscal Year":
                i += 1
                continue
            title, production_company = self._split_heading(raw_heading)
            if not is_probable_project_title(title):
                i += 1
                continue
            fields: dict[str, str] = {}
            j = i + 1
            while j < len(lines):
                label = lines[j]
                if label not in KNOWN_FIELD_LABELS:
                    break
                if j + 1 >= len(lines):
                    break
                fields[label] = lines[j + 1]
                j += 2
            content_type = fields.get("Content Type", "")
            program = fields.get("Program", "")
            activity = fields.get("Activity", "")
            if not self._looks_like_film_project(content_type, program):
                i = j
                continue
            if activity and activity.lower() not in {"production", "development", "predevelopment"}:
                i = j
                continue
            normalized = title.lower()
            if normalized in seen_titles:
                i = j
                continue
            seen_titles.add(normalized)
            items.append(
                ExtractedFilm(
                    title=title,
                    source_name=source_meta["name"],
                    source_url=source_meta["url"],
                    source_tier=source_meta["tier"],
                    source_type=source_meta["source_type"],
                    status="funded",
                    confidence_score=90,
                    date_detected=datetime.utcnow(),
                    project_type=self._infer_project_type(content_type),
                    country="Canada",
                    region="Canada",
                    province_or_state=fields.get("Region"),
                    production_company=production_company,
                    budget_text="Unknown",
                    notes=f"Extracted from CMF funded projects database ({program or 'program unspecified'}).",
                )
            )
            i = j
        return items

    def _split_heading(self, raw_heading: str) -> tuple[str, str | None]:
        heading = " ".join(raw_heading.split()).strip()
        match = re.match(r"^(?P<title>.+?)\s+Production\s+(?P<company>.+)$", heading)
        if not match:
            return heading, None
        return match.group("title").strip(), match.group("company").strip()

    def _looks_like_film_project(self, content_type: str, program: str) -> bool:
        lowered_content_type = content_type.lower()
        lowered_program = program.lower()
        if any(fragment in lowered_content_type for fragment in DISALLOWED_CONTENT_TYPE_FRAGMENTS):
            return False
        if any(fragment in lowered_content_type for fragment in ALLOWED_CONTENT_TYPE_FRAGMENTS):
            return True
        return any(fragment in lowered_program for fragment in ALLOWED_PROGRAM_FRAGMENTS)

    def _infer_project_type(self, content_type: str) -> str | None:
        lowered = content_type.lower()
        if any(fragment in lowered for fragment in ("series", "television", "tv", "episodic")):
            return "series"
        if "documentary" in lowered:
            return "documentary_feature" if "feature" in lowered else "documentary_series"
        if "animation" in lowered and any(fragment in lowered for fragment in ("series", "television", "tv", "episodic")):
            return "animated_series"
        if any(fragment in lowered for fragment in ("feature", "film")):
            return "feature_film"
        return None
