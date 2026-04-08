from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from film_intelligence_agent.db.base import Base


def new_id() -> str:
    return str(uuid.uuid4())


class Film(Base):
    __tablename__ = "films"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(500), index=True)
    normalized_title: Mapped[str] = mapped_column(String(500), index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(32), index=True)
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(64), default="unknown")
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
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0)
    opportunity_score_breakdown: Mapped[dict | None] = mapped_column(JSON)
    budget_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    budget_currency: Mapped[str | None] = mapped_column(String(8))
    budget_text: Mapped[str] = mapped_column(String(128), default="Unknown")
    budget_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(32), index=True)
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    match_confidence: Mapped[float | None] = mapped_column(Float)
    match_method: Mapped[str | None] = mapped_column(String(64))
    is_known_collaborator: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(32))
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class FilmPerson(Base):
    __tablename__ = "film_people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    role: Mapped[str] = mapped_column(String(128), index=True)
    confidence: Mapped[float | None] = mapped_column(Float)


class FilmCompany(Base):
    __tablename__ = "film_companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    role: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[float | None] = mapped_column(Float)


class Collaborator(Base):
    __tablename__ = "collaborators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), unique=True, index=True)
    shared_project_names: Mapped[list[str] | None] = mapped_column(JSON)
    shared_project_count: Mapped[int] = mapped_column(Integer, default=0)
    last_collaboration_date: Mapped[date | None] = mapped_column(Date)


class CollaboratorMatch(Base):
    __tablename__ = "collaborator_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    overlap_type: Mapped[str] = mapped_column(String(64))
    match_confidence: Mapped[float] = mapped_column(Float)
    shared_project_names: Mapped[list[str] | None] = mapped_column(JSON)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)


class WarmPath(Base):
    __tablename__ = "warm_paths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    target_person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    intermediary_person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), index=True)
    path_description: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str | None] = mapped_column(ForeignKey("films.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(128))
    source_tier: Mapped[str] = mapped_column(String(64))
    raw_snapshot_hash: Mapped[str | None] = mapped_column(String(128))
    snippet: Mapped[str | None] = mapped_column(Text)
    extraction_payload: Mapped[dict | None] = mapped_column(JSON)


class FundingRecord(Base):
    __tablename__ = "funding_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    film_id: Mapped[str] = mapped_column(ForeignKey("films.id"), index=True)
    funding_source: Mapped[str] = mapped_column(String(255))
    funding_program: Mapped[str | None] = mapped_column(String(255))
    funding_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    funding_currency: Mapped[str | None] = mapped_column(String(8))
    funding_stage: Mapped[str | None] = mapped_column(String(64))


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    summary_text: Mapped[str | None] = mapped_column(Text)
    report_html: Mapped[str | None] = mapped_column(Text)
    report_text: Mapped[str | None] = mapped_column(Text)
    notion_page_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="generated")


class ReportItem(Base):
    __tablename__ = "report_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    weekly_report_id: Mapped[str] = mapped_column(ForeignKey("weekly_reports.id"), index=True)
    film_id: Mapped[str | None] = mapped_column(ForeignKey("films.id"), index=True)
    section_name: Mapped[str] = mapped_column(String(128))
    rank: Mapped[int | None] = mapped_column(Integer)
    item_payload: Mapped[dict] = mapped_column(JSON)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pipeline_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_metadata: Mapped[dict | None] = mapped_column(JSON)
    error_summary: Mapped[str | None] = mapped_column(Text)


class AppConfig(Base):
    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
