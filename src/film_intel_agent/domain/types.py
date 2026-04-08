from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(slots=True)
class RawFetchResult:
    source_name: str
    source_url: str
    status_code: int
    content_type: str | None
    html: str | None = None
    text: str | None = None
    fetched_at: datetime | None = None
    snapshot_hash: str | None = None
    cache_path: str | None = None


@dataclass(slots=True)
class ExtractedPerson:
    full_name: str
    role: str
    imdb_id: str | None = None
    imdb_url: str | None = None
    confidence: float | None = None
    is_known_collaborator: bool = False
    shared_projects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExtractedFilm:
    title: str
    source_name: str
    source_url: str
    source_tier: str
    source_type: str
    status: str
    confidence_score: int
    date_detected: datetime
    project_type: str | None = None
    country: str | None = None
    region: str | None = None
    province_or_state: str | None = None
    production_company: str | None = None
    genre: str | None = None
    subgenre: str | None = None
    notes: str | None = None
    imdb_id: str | None = None
    imdb_url: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    budget_currency: str | None = None
    budget_text: str = "Unknown"
    budget_confidence: float | None = None
    people: list[ExtractedPerson] = field(default_factory=list)
    supporting_sources: list[dict] = field(default_factory=list)
    funding_records: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class CollaboratorEdge:
    person_name: str
    person_imdb_id: str | None
    person_imdb_url: str | None
    role: str
    project_title: str
    project_imdb_id: str | None
    project_imdb_url: str | None
    release_date: date | None
    match_confidence: float
    match_method: str
