from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.parsers.base import SourceParser
from film_intelligence_agent.parsers.sources.common import clean_candidate_title, extract_title_from_container, has_project_signal
from film_intelligence_agent.utils.quality import is_probable_project_title


POSSESSIVE_TITLE_PATTERN = re.compile(
    r"(?:[A-Z][A-Za-zÀ-ÿ'’.-]+(?:\s+[A-Z][A-Za-zÀ-ÿ'’.-]+){0,4})[’']s\s+"
    r"([A-Z][A-Za-zÀ-ÿ0-9'’:-]+(?:\s+[A-Z][A-Za-zÀ-ÿ0-9'’:-]+){0,6})"
)
DESCRIPTOR_TITLE_PATTERN = re.compile(
    r"(?i:(?:feature documentary|documentary|short film|feature film|series))\s+"
    r"([A-Z][^.:;]+?)(?=\s(?:premiere|premieres|selected|playing|goes|wins|is|at|for|to)\b|[.:])",
)
SLUG_STOP_MARKERS = (
    "-at-",
    "-available-",
    "-oscar-",
    "-theatrical-",
    "-selected-",
    "-winner-",
    "-playing-",
    "-premiere-",
    "-premieres-",
    "-goes-",
)
SLUG_PREFIX_BLACKLIST = ("nfb-", "cynthia-", "board-", "canada-")
TITLE_FRAGMENT_BLACKLIST = (
    "from oscar nominated director",
    "for their national film board of canada",
    "national film board of canada",
)
TITLE_PREFIX_BLACKLIST = ("from ", "for ", "their ", "new ", "part ")


class NFBNewsParser(SourceParser):
    def parse(self, html: str, source_meta: dict) -> list[ExtractedFilm]:
        soup = BeautifulSoup(html, "lxml")
        items: list[ExtractedFilm] = []
        seen_titles: set[str] = set()
        for article in soup.select(".gw-gopf-col-wrap, .gw-gopf-post, article, li, .news, .gc-nws"):
            headline = extract_title_from_container(article, (".gw-gopf-post-title h2 a", "h1", "h2", "h3", "a"))
            if not headline:
                continue
            context_text = article.get_text(" ", strip=True)
            if not has_project_signal(context_text):
                continue
            link = article.select_one(".gw-gopf-post-title a, h1 a, h2 a, h3 a, a")
            item_url = link.get("href") if link and link.get("href") else source_meta["url"]
            for title in self._extract_project_titles(headline, context_text, item_url):
                normalized = title.lower()
                if normalized in seen_titles:
                    continue
                seen_titles.add(normalized)
                items.append(
                    ExtractedFilm(
                        title=title,
                        source_name=source_meta["name"],
                        source_url=item_url,
                        source_tier=source_meta["tier"],
                        source_type=source_meta["source_type"],
                        status=self._infer_status(context_text),
                        confidence_score=84,
                        date_detected=datetime.utcnow(),
                        project_type=self._infer_project_type(context_text),
                        country="Canada",
                        region="Canada",
                        budget_text="Unknown",
                        notes="Extracted from NFB Media Space press release with explicit project signal.",
                    )
                )
        return items

    def _extract_project_titles(self, headline: str, context_text: str, item_url: str) -> list[str]:
        candidates: list[str] = []
        slug_title = self._title_from_url(item_url)
        if slug_title:
            candidates.append(slug_title)
        for match in POSSESSIVE_TITLE_PATTERN.findall(headline):
            candidate = clean_candidate_title(match)
            if is_probable_project_title(candidate):
                candidates.append(candidate)
        if not slug_title:
            for match in DESCRIPTOR_TITLE_PATTERN.findall(f"{headline}. {context_text}"):
                candidate = clean_candidate_title(match)
                if self._is_usable_extracted_title(candidate):
                    candidates.append(candidate)
        if is_probable_project_title(headline) and len(headline.split()) <= 8:
            candidate = clean_candidate_title(headline)
            if self._is_usable_extracted_title(candidate):
                candidates.append(candidate)
        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    def _title_from_url(self, item_url: str) -> str | None:
        slug = urlparse(item_url).path.rstrip("/").split("/")[-1].strip().lower()
        if not slug or slug.startswith(SLUG_PREFIX_BLACKLIST):
            return None
        slug = re.sub(r"-20\d{2}$", "", slug)
        for marker in SLUG_STOP_MARKERS:
            if marker in slug:
                slug = slug.split(marker, 1)[0]
                break
        candidate = clean_candidate_title(slug.replace("-", " ").title()).replace("(Nfb)", "").strip()
        if self._is_usable_extracted_title(candidate):
            return candidate
        return None

    def _is_usable_extracted_title(self, candidate: str) -> bool:
        cleaned = clean_candidate_title(candidate).replace("(NFB)", "").strip(" .:-")
        lowered = cleaned.lower()
        if any(lowered.startswith(prefix) for prefix in TITLE_PREFIX_BLACKLIST):
            return False
        if any(fragment in lowered for fragment in TITLE_FRAGMENT_BLACKLIST):
            return False
        if len(cleaned.split()) == 1 and "'" in cleaned:
            return False
        return is_probable_project_title(cleaned)

    def _infer_project_type(self, text: str) -> str | None:
        lowered = text.lower()
        if "series" in lowered:
            return "series"
        if "feature documentary" in lowered:
            return "documentary_feature"
        if "documentary" in lowered:
            return "documentary_series"
        if "short film" in lowered:
            return "short_film"
        if "feature film" in lowered or "feature" in lowered:
            return "feature_film"
        return None

    def _infer_status(self, text: str) -> str:
        lowered = text.lower()
        if any(keyword in lowered for keyword in ("in production", "production", "new feature documentary")):
            return "production"
        if any(keyword in lowered for keyword in ("selected", "premiere", "playing", "goes global", "available worldwide")):
            return "greenlit"
        return "unknown"
