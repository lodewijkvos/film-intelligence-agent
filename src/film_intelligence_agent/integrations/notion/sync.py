from __future__ import annotations

import logging
import os

from sqlalchemy import desc, select

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.db.models import Film, ReportItem, WeeklyReport
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.integrations.notion.client import get_notion_client
from film_intelligence_agent.reports.render import SECTION_EMPTY_STATES, SECTION_ORDER
from film_intelligence_agent.services.config_store import ConfigStore
from film_intelligence_agent.utils.normalize import normalize_title
from film_intelligence_agent.utils.quality import is_probable_project_title, is_probable_project_title_normalized

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
            films = [
                film
                for film in session.scalars(select(Film).order_by(desc(Film.last_seen_at)).limit(limit * 5))
                if is_probable_project_title(film.title)
                and is_probable_project_title_normalized(normalize_title(film.title))
            ][:limit]
        self._clear_existing_film_pages()
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

    def _clear_existing_film_pages(self) -> None:
        archived_ids: set[str] = set()

        def archive_from_query(method: str, identifier_key: str, identifier_value: str) -> None:
            endpoint = getattr(self.client, method, None)
            if endpoint is None or not hasattr(endpoint, "query"):
                return
            next_cursor: str | None = None
            while True:
                payload = {identifier_key: identifier_value, "page_size": 100}
                if next_cursor:
                    payload["start_cursor"] = next_cursor
                response = endpoint.query(**payload)
                results = response.get("results", [])
                for page in results:
                    page_id = page["id"]
                    if page_id in archived_ids:
                        continue
                    self.client.pages.update(page_id=page_id, archived=True)
                    archived_ids.add(page_id)
                if not response.get("has_more"):
                    break
                next_cursor = response.get("next_cursor")

        archive_from_query("data_sources", "data_source_id", self.films_database_id)

        try:
            data_source = self.client.data_sources.retrieve(data_source_id=self.films_database_id)
            parent = data_source.get("parent", {})
            parent_database_id = parent.get("database_id") if parent.get("type") == "database_id" else None
        except Exception:
            parent_database_id = None

        if parent_database_id:
            archive_from_query("databases", "database_id", parent_database_id)

    def create_report_page(self, report_id: str) -> str | None:
        if not self.settings.notion_parent_page_id:
            return None
        with db_session() as session:
            report = session.scalar(select(WeeklyReport).where(WeeklyReport.id == report_id))
            report_items = list(
                session.scalars(
                    select(ReportItem).where(ReportItem.weekly_report_id == report_id).order_by(ReportItem.section_name, ReportItem.rank)
                )
            )
        if report is None:
            return None
        items_by_section: dict[str, list[ReportItem]] = {section_name: [] for section_name in SECTION_ORDER}
        for item in report_items:
            items_by_section.setdefault(item.section_name, []).append(item)

        children: list[dict] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": report.summary_text or ""}}]},
            },
            {"object": "block", "type": "divider", "divider": {}},
        ]

        weekly_summary_lines = [
            f"Week of {report.report_date.strftime('%B %d, %Y')}",
            f"Dry run: {'Yes' if report.dry_run else 'No'}",
            "This page is intended to mirror the weekly email structure.",
        ]

        def text_part(content: str, url: str | None = None, bold: bool = False) -> dict:
            annotations = {
                "bold": bold,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            }
            text = {"content": content}
            if url and url != "Unknown":
                text["link"] = {"url": url}
            return {"type": "text", "text": text, "annotations": annotations}

        def line_parts(label: str, value: str, url: str | None = None) -> list[dict]:
            return [text_part(f"{label}: ", bold=True), text_part(value or "Unknown", url=url), text_part("\n")]

        def producer_parts(producer_links: list[dict]) -> list[dict]:
            if not producer_links:
                return line_parts("Producers", "Unknown")
            parts = [text_part("Producers: ", bold=True)]
            for index, producer in enumerate(producer_links):
                if index:
                    parts.append(text_part(", "))
                parts.append(text_part(producer.get("name") or "Unknown", url=producer.get("url")))
            parts.append(text_part("\n"))
            return parts

        for section_name in SECTION_ORDER:
            children.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": section_name}}]},
                }
            )
            if section_name == "Weekly Summary":
                for line in weekly_summary_lines:
                    children.append(
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line}}]},
                        }
                    )
                continue
            section_items = items_by_section.get(section_name, [])
            if not section_items:
                children.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": SECTION_EMPTY_STATES[section_name]}}]
                        },
                    }
                )
                continue
            for item in section_items:
                payload = item.item_payload or {}
                title = payload.get("title") or "Untitled"
                status = payload.get("status") or "Unknown"
                budget = payload.get("budget") or "Unknown"
                country = payload.get("country") or "Unknown"
                region = payload.get("region") or "Unknown"
                production_company = payload.get("production_company") or "Unknown"
                director = payload.get("director") or "Unknown"
                editor = payload.get("editor") or "Unknown"
                composer = payload.get("composer") or "Unknown"
                director_note = payload.get("director_note")
                editor_note = payload.get("editor_note")
                composer_note = payload.get("composer_note")
                imdb_link = payload.get("title_url")
                source_name = payload.get("source_name") or "Unknown"
                source_url = payload.get("source_url") or "Unknown"
                production_company_url = payload.get("production_company_url")
                director_url = payload.get("director_url")
                editor_url = payload.get("editor_url")
                composer_url = payload.get("composer_url")
                producer_links = payload.get("producer_links") or []
                producer_notes = payload.get("producer_notes") or {}
                opportunity_score = payload.get("opportunity_score") or 0
                why_this_matters = payload.get("why_this_matters") or "Needs manual review."
                recent_sources = payload.get("recent_sources") or []
                children.append(
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {"rich_text": [text_part(title, url=imdb_link, bold=True)]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Budget", budget)[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Country", country)[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Region", region)[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Production Company", production_company, url=production_company_url)[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": (line_parts("Director", director, url=director_url)[:-1] + ([text_part(f" {director_note}")] if director_note else []))},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": (line_parts("Editor", editor, url=editor_url)[:-1] + ([text_part(f" {editor_note}")] if editor_note else []))},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": (line_parts("Composer", composer, url=composer_url)[:-1] + ([text_part(f" {composer_note}")] if composer_note else []))},
                    }
                )
                producer_children = []
                if producer_links:
                    for producer in producer_links:
                        producer_name = producer.get("name") or "Unknown"
                        producer_line = [text_part(producer_name, url=producer.get("url"))]
                        if producer_notes.get(producer_name):
                            producer_line.append(text_part(f" {producer_notes[producer_name]}"))
                        producer_children.append(
                            {
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {"rich_text": producer_line},
                            }
                        )
                else:
                    producer_children.append(
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [text_part("Unknown")]},
                        }
                    )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [text_part("Producers", bold=True)]},
                        "children": producer_children[:10],
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Status", status)[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Opportunity Score", str(opportunity_score))[:-1]},
                    }
                )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": line_parts("Why this matters", why_this_matters)[:-1]},
                    }
                )
                source_children = []
                for source in recent_sources:
                    source_children.append(
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [text_part(source.get("name") or "Unknown", url=source.get("url"))]},
                        }
                    )
                if not source_children:
                    source_children.append(
                        {
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {"rich_text": [text_part("No recent sources attached yet.")]},
                        }
                    )
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [text_part("Recent Press / Sources", bold=True)]},
                        "children": source_children[:10],
                    }
                )
                children.append({"object": "block", "type": "divider", "divider": {}})

        response = self.client.pages.create(
            parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": f"Weekly Report {report.report_date.isoformat()}"}}]
            },
            children=children[:100],
        )
        return response["id"]
