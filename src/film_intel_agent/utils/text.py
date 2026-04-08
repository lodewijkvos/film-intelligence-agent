from __future__ import annotations

import re


LEADING_ARTICLES = ("the ", "a ", "an ")
WORKING_TITLE_PREFIXES = ("untitled ", "project ", "working title ")


def normalize_title(value: str) -> str:
    normalized = re.sub(r"[^\w\s]", " ", value.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    for article in LEADING_ARTICLES:
        if normalized.startswith(article):
            normalized = normalized[len(article) :]
    for prefix in WORKING_TITLE_PREFIXES:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.strip()


def normalize_name(value: str) -> str:
    normalized = re.sub(r"[^\w\s]", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", normalized)
