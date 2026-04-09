from __future__ import annotations


NOISE_TITLE_FRAGMENTS = (
    "about us",
    "about the industry",
    "bc film commission",
    "calendar",
    "close",
    "community resources",
    "contact us",
    "contacts",
    "creative pathways",
    "film permit",
    "filming on location",
    "funding programs",
    "industries",
    "industry resources",
    "information sessions",
    "location library",
    "motion picture contacts",
    "motion picture tax credits",
    "news",
    "open",
    "production equipment",
    "protocols",
    "reel green",
    "regions",
    "resources",
    "sector-wide service",
    "stages",
    "studio facilities",
    "studio zones",
    "talent + labour",
)


def is_probable_project_title(title: str) -> bool:
    cleaned = " ".join(title.split()).strip()
    if len(cleaned) < 2 or len(cleaned) > 180:
        return False
    lowered = cleaned.lower()
    if any(fragment in lowered for fragment in NOISE_TITLE_FRAGMENTS):
        return False
    if cleaned.count(" + ") >= 1:
        return False
    return True
