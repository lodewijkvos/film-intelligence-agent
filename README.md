# Film Intelligence Agent

Production-ready film intelligence agent for Lodewijk Vos.

## What It Does

This system runs a weekly Canada-first film discovery workflow with a separate IMDb collaborator-ingestion pass first. It:

- updates a canonical PostgreSQL/Supabase database
- maintains a collaborator graph rooted in Lodewijk Vos' credits
- discovers and enriches film opportunities from official and trade sources
- syncs review-friendly records into Notion
- generates a decision-oriented weekly report
- sends a dry-run or live report email

## Core Workflow

1. Ingest IMDb Pro/public collaborator graph
2. Ingest official Canadian funding and production sources
3. Ingest secondary Canadian/U.S./Europe sources
4. Normalize, dedupe, score, and flag review items
5. Sync Notion databases and create the weekly report page
6. Send HTML and text report email

## Runtime

- Python 3.11+
- Supabase/PostgreSQL as canonical storage
- GitHub Actions for weekly scheduling
- Notion as sync and review layer
- Resend for email delivery

## Local Setup

1. Create a Python 3.11 virtual environment
2. Install dependencies: `pip install -e .[dev]`
3. Copy `.env.example` to `.env` and fill in secrets
4. Initialize the schema: `film-intel initdb`
5. Optionally create Notion databases: `film-intel setup-notion`
6. Run a dry-run report: `film-intel run-weekly --dry-run`

## Key Commands

- `film-intel initdb`
- `film-intel ingest-imdb`
- `film-intel ingest-sources`
- `film-intel run-weekly --dry-run`
- `film-intel sync-notion`

## Notes

- IMDb ingestion is implemented as a hybrid pipeline with a public-page fallback and manual-review hooks.
- Notion is intentionally not treated as the source of truth.
- Official Canadian sources outrank trades in canonical record selection.
