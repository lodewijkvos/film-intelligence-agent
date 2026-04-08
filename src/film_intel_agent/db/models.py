from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from film_intel_agent.db.base import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Film(Base, TimestampMixin):
    __tablename__ = "films"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(500), index=True)
    normalized_title: Mapped[str] = mapped_column(String(500), index=True)
    alternate_title: Mapped[str | None] = mapped_column(String(500))
    imdb_id: Mapped[str | None] = mapped_column(String(32), index=True)
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    project_type: Mapped[str | None] = mapped_column(String(64))
    genre: Mapped[str | None] = mapped_column(String(128))
    subgenre: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128), index=True)
    region: Mapped[str | None] = mapped_column(String(128), index=True)
    province_or_state: Mapped[str | None] = mapped_column(String(128))
    production_company: Mapped[str | None] = mapped_column(String(255))
    source_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(1000))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    data_confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    opportunity_score_breakdown: Mapped[dict | None] = mapped_column(JSON)
    date_detected: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    source_tier: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[str | None] = mapped_column(String(128))
    canada_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    budget_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    budget_currency: Mapped[str | None] = mapped_column(String(8))
    budget_text: Mapped[str] = mapped_column(String(128), default="Unknown")
    budget_confidence: Mapped[float | None] = mapped_column(Float)

    film_people: Mapped[list["FilmPerson"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    film_companies: Mapped[list["FilmCompany"]] = relationship(
        back_populates="film", cascade="all, delete-orphan"
    )


class Person(Base, TimestampMixin):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(32), index=True)
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    match_confidence: Mapped[float | None] = mapped_column(Float)
    match_method: Mapped[str | None] = mapped_column(String(64))
    is_known_collaborator: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    film_people: Mapped[list["FilmPerson"]] = relationship(back_populates="person", cascade="all, delete-orphan")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    country: Mapped[str | None] = mapped_column(String(128))
    imdb_id: Mapped[str | None] = mapped_column(String(32))
    imdb_url: Mapped[str | None] = mapped_column(String(500))

    film_companies: Mapped[list["FilmCompany"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class FilmPerson(Base, TimestampMixin):
    __tablename__ = "film_people"
    __table_args__ = (UniqueConstraint("film_id", "person_id", "role", name="uq_film_person_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    role: Mapped[str] = mapped_column(String(128), index=True)
    billing_order: Mapped[int | None] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id"))
    confidence: Mapped[float | None] = mapped_column(Float)

    film: Mapped["Film"] = relationship(back_populates="film_people")
    person: Mapped["Person"] = relationship(back_populates="film_people")


class FilmCompany(Base, TimestampMixin):
    __tablename__ = "film_companies"
    __table_args__ = (UniqueConstraint("film_id", "company_id", "role", name="uq_film_company_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    role: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[float | None] = mapped_column(Float)

    film: Mapped["Film"] = relationship(back_populates="film_companies")
    company: Mapped["Company"] = relationship(back_populates="film_companies")


class Collaborator(Base, TimestampMixin):
    __tablename__ = "collaborators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), unique=True, index=True)
    shared_project_names: Mapped[list[str] | None] = mapped_column(JSON)
    shared_project_count: Mapped[int] = mapped_column(Integer, default=0)
    last_collaboration_date: Mapped[date | None] = mapped_column(Date)
    role_summary: Mapped[list[str] | None] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(64), default="imdb")


class CollaboratorMatch(Base, TimestampMixin):
    __tablename__ = "collaborator_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    collaborator_id: Mapped[str] = mapped_column(ForeignKey("collaborators.id"), index=True)
    overlap_type: Mapped[str] = mapped_column(String(64), index=True)
    match_confidence: Mapped[float] = mapped_column(Float)
    shared_project_names: Mapped[list[str] | None] = mapped_column(JSON)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class WarmPath(Base, TimestampMixin):
    __tablename__ = "warm_paths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    target_person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    intermediary_person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    path_description: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)


class SourceRecord(Base, TimestampMixin):
    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str | None] = mapped_column(ForeignKey("films.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(128))
    source_tier: Mapped[str] = mapped_column(String(64))
    raw_snapshot_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    raw_html_path: Mapped[str | None] = mapped_column(String(500))
    raw_text_path: Mapped[str | None] = mapped_column(String(500))
    snippet: Mapped[str | None] = mapped_column(Text)
    publish_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reliability_score: Mapped[int | None] = mapped_column(Integer)
    extraction_payload: Mapped[dict | None] = mapped_column(JSON)


class FundingRecord(Base, TimestampMixin):
    __tablename__ = "funding_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    funding_source: Mapped[str] = mapped_column(String(255))
    funding_program: Mapped[str | None] = mapped_column(String(255))
    funding_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    funding_currency: Mapped[str | None] = mapped_column(String(8))
    funding_stage: Mapped[str | None] = mapped_column(String(64))
    fiscal_year: Mapped[str | None] = mapped_column(String(32))
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id"))


class WeeklyReport(Base, TimestampMixin):
    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    report_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    run_type: Mapped[str] = mapped_column(String(32), default="scheduled")
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    summary_text: Mapped[str | None] = mapped_column(Text)
    report_html: Mapped[str | None] = mapped_column(Text)
    report_text: Mapped[str | None] = mapped_column(Text)
    notion_page_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="generated")


class ReportItem(Base, TimestampMixin):
    __tablename__ = "report_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    weekly_report_id: Mapped[str] = mapped_column(ForeignKey("weekly_reports.id"), index=True)
    film_id: Mapped[str | None] = mapped_column(ForeignKey("films.id"), index=True)
    section_name: Mapped[str] = mapped_column(String(128), index=True)
    rank: Mapped[int | None] = mapped_column(Integer)
    item_payload: Mapped[dict] = mapped_column(JSON)


class IngestionRun(Base, TimestampMixin):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    pipeline_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_metadata: Mapped[dict | None] = mapped_column(JSON)
    error_summary: Mapped[str | None] = mapped_column(Text)
