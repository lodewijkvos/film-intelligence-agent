from __future__ import annotations


NOISE_TITLE_FRAGMENTS = (
    "about creative bc",
    "about the sector",
    "about us",
    "about the industry",
    "apply online",
    "bc film commission",
    "facebook",
    "book publishing",
    "calendar",
    "careers",
    "close",
    "code of conduct",
    "community resources",
    "contact us",
    "contacts",
    "creative pathways",
    "creative sector",
    "cross border services",
    "deadlines",
    "film permit",
    "film incentive bc",
    "filming on location",
    "follow ontario creates",
    "funding available",
    "funding recipients",
    "funding programs",
    "greater vancouver film offices",
    "guidelines and application form",
    "industries",
    "industry resources",
    "information sessions",
    "in production",
    "instagram",
    "interactive digital media",
    "linkedin",
    "location library",
    "logos",
    "magazine publishing",
    "media room",
    "motion picture contacts",
    "motion picture tax credits",
    "motion picture",
    "multi-creative industry services",
    "motion picture contacts",
    "motion picture tax credits",
    "news",
    "open",
    "overview",
    "production equipment",
    "production credits",
    "production register",
    "production services tax credit",
    "protocols",
    "register a production",
    "reel green",
    "regions",
    "reports",
    "research",
    "resources",
    "sector-wide service",
    "social",
    "spotify",
    "stay informed",
    "stages",
    "stories",
    "studio facilities",
    "studio zones",
    "talent + labour",
    "application process",
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
    if lowered in {
        "linkedin",
        "instagram",
        "facebook",
        "spotify",
        "logos",
        "reports",
        "overview",
        "research",
        "stories",
        "regions",
    }:
        return False
    return True
