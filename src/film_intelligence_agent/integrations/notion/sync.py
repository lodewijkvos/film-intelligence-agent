from __future__ import annotations

import logging
import os

from sqlalchemy import desc, select

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.db.models import Film, WeeklyReport
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.integrations.notion.client import get_notion_client
from film_intelligence_agent.services.config_store import ConfigStore

logger = logging.getLogger(__name__)


class NotionSyncService:
    def __init__(self, films_database_id: str | None = None, people_database_id: str | None = None) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()
        store = ConfigStore()
        self.films_database_id = (
            films_database_id
            or self.settings.notion_films_database_id
            or store.get("notion_films_database_id")
        )
        self.people_database_id = (
            people_database_id
            or self.settings.notion_people_database_id
            or store.get("notion_people_database_id")
        )

    def sync_films(self, limit: int = 25) -> None:
        if not self.films_database_id:
            logger.info("Notion film sync skipped: no films database id configured")
            return
        data_source = self.client.data_sources.retrieve(data_source_id=self.films_database_id)
        properties = data_source.get("properties", {}) or {}
        logger.info("Notion film database properties: %s", list(properties.keys()))
        title_property = next((name for name, meta in properties.items() if meta.get("type") == "title"), None)
        status_property = "Status" if "Status" in properties else None
        confidence_property = "Confidence" if "Confidence" in properties else None
        opportunity_property = "Opportunity" if "Opportunity" in properties else None
        country_property = "Country" if "Country" in properties else None
        budget_property = "BudgetRange" if "BudgetRange" in properties else None
        source_url_property = "SourceURL" if "SourceURL" in properties else None
        if not title_property:
            logger.info("Notion film sync skipped: no title property found on database %s", self.films_database_id)
            return
        with db_session() as session:
            films = list(session.scalars(select(Film).order_by(desc(Film.last_seen_at)).limit(limit)))
        synced_count = 0
        for film in films:
            existing = self.client.data_sources.query(
                data_source_id=self.films_database_id,
                filter={
                    "property": title_property,
                    "title": {"equals": film.title[:200]},
                },
                page_size=1,
            )
            if existing.get("results"):
                continue
            notion_properties = {
                title_property: {"title": [{"text": {"content": film.title[:200]}}]},
            }
            if status_property:
                notion_properties[status_property] = {
                    "rich_text": [{"text": {"content": (film.status or "Unknown")[:200]}}]
                }
            if confidence_property:
                notion_properties[confidence_property] = {"number": film.data_confidence_score}
            if opportunity_property:
                notion_properties[opportunity_property] = {"number": film.opportunity_score}
            if country_property:
                notion_properties[country_property] = {
                    "rich_text": [{"text": {"content": (film.country or "Unknown")[:200]}}]
                }
            if budget_property:
                notion_properties[budget_property] = {
                    "rich_text": [{"text": {"content": (film.budget_text or "Unknown")[:200]}}]
                }
            if source_url_property:
                notion_properties[source_url_property] = {"url": film.source_url}
            self.client.pages.create(parent={"data_source_id": self.films_database_id}, properties=notion_properties)
            synced_count += 1
        logger.info(
            "Notion film sync complete: database_id=%s synced_count=%s candidate_count=%s",
            self.films_database_id,
            synced_count,
            len(films),
        )
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as handle:
                handle.write(
                    "\n".join(
                        [
                            "## Notion Sync",
                            f"- Films database id: `{self.films_database_id}`",
                            f"- Synced film rows this run: `{synced_count}`",
                            f"- Candidate film rows considered: `{len(films)}`",
                            "",
                        ]
                    )
                )

    def create_report_page(self, report_id: str) -> str | None:
        if not self.settings.notion_parent_page_id:
            return None
        with db_session() as session:
            report = session.scalar(select(WeeklyReport).where(WeeklyReport.id == report_id))
        if report is None:
            return None
        response = self.client.pages.create(
            parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": f"Weekly Report {report.report_date.isoformat()}"}}]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": report.summary_text or ""}}]},
                }
            ],
        )
        return response["id"]
