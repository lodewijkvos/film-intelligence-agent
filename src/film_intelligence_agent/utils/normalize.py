from __future__ import annotations

import re


def normalize_title(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for prefix in ("the ", "a ", "an ", "untitled ", "project ", "working title "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned.strip()


def normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)
