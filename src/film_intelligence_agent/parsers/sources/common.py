from __future__ import annotations

from bs4 import Tag

from film_intelligence_agent.utils.quality import is_probable_project_title


PROJECT_SIGNAL_KEYWORDS = (
    "greenlit",
    "green light",
    "funded",
    "funding",
    "selected",
    "approved",
    "support",
    "in production",
    "begins shooting",
    "starts shooting",
    "principal photography",
    "filming",
    "production",
    "feature film",
    "documentary",
    "co-production",
    "financing",
)


def clean_candidate_title(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip(" -:\u2013\u2014|")


def extract_title_from_container(container: Tag, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        node = container.select_one(selector)
        if not node:
            continue
        candidate = clean_candidate_title(node.get_text(" ", strip=True))
        if is_probable_project_title(candidate):
            return candidate
    return None


def has_project_signal(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in PROJECT_SIGNAL_KEYWORDS)
