from __future__ import annotations

from pathlib import Path

from film_intelligence_agent.imdb.ingestion import IMDbIngestionService
from film_intelligence_agent.integrations.notion.setup import NotionSetupService
from film_intelligence_agent.integrations.notion.sync import NotionSyncService
from film_intelligence_agent.services.discovery import DiscoveryService
from film_intelligence_agent.services.films import FilmPersistenceService
from film_intelligence_agent.services.reports import WeeklyReportService


class WeeklyOrchestrator:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def run(self, dry_run: bool = True) -> None:
        IMDbIngestionService().run()
        extracted = DiscoveryService(self.config_path).collect()
        FilmPersistenceService().upsert(extracted)
        report = WeeklyReportService().generate(dry_run=dry_run)
        database_ids = NotionSetupService().ensure_databases()
        notion = NotionSyncService(
            films_database_id=database_ids.get("films_database_id"),
            people_database_id=database_ids.get("people_database_id"),
        )
        notion.create_report_page(report.id)
        notion.sync_films()
        if not dry_run:
            WeeklyReportService().send(dry_run=False)
