from __future__ import annotations

from pathlib import Path

import typer

from film_intelligence_agent.imdb.ingestion import IMDbIngestionService
from film_intelligence_agent.integrations.notion.setup import NotionSetupService
from film_intelligence_agent.integrations.notion.sync import NotionSyncService
from film_intelligence_agent.services.bootstrap import healthcheck, init_db
from film_intelligence_agent.services.discovery import DiscoveryService
from film_intelligence_agent.services.films import FilmPersistenceService
from film_intelligence_agent.services.orchestrator import WeeklyOrchestrator
from film_intelligence_agent.utils.logging import configure_logging
from film_intelligence_agent.config.settings import get_settings

app = typer.Typer(no_args_is_help=True)


def boot() -> None:
    configure_logging(get_settings().log_level)


@app.command("init-db")
def init_db_cmd() -> None:
    boot()
    init_db()
    typer.echo("Database initialized.")


@app.command()
def check() -> None:
    boot()
    healthcheck()
    typer.echo("Database OK.")


@app.command("setup-notion")
def setup_notion_cmd() -> None:
    boot()
    created = NotionSetupService().ensure_databases()
    typer.echo(f"Created: {created}")


@app.command("ingest-imdb")
def ingest_imdb_cmd() -> None:
    boot()
    edges = IMDbIngestionService().run()
    typer.echo(f"Ingested {len(edges)} IMDb edges.")


@app.command("ingest-sources")
def ingest_sources_cmd() -> None:
    boot()
    config_path = Path("config/film_greenlight_scraper_spec.yaml")
    films = DiscoveryService(config_path).collect()
    FilmPersistenceService().upsert(films)
    typer.echo(f"Ingested {len(films)} source records.")


@app.command("sync-notion")
def sync_notion_cmd() -> None:
    boot()
    NotionSyncService().sync_films()
    typer.echo("Notion sync complete.")


@app.command("run-weekly")
def run_weekly_cmd(
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Dry run or live send."),
) -> None:
    boot()
    WeeklyOrchestrator(Path("config/film_greenlight_scraper_spec.yaml")).run(dry_run=dry_run)
    typer.echo("Weekly workflow complete.")
