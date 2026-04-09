# Film Intelligence Agent

Production-ready film intelligence agent for Lodewijk Vos.

## Outcome

This system is designed to:

- run every Monday at 9:00 a.m. America/Toronto
- ingest Lo's collaborator graph from IMDb first
- discover and score film and series opportunities with Canada-first priority
- keep canonical state in PostgreSQL/Supabase
- sync selected records and weekly reports to Notion
- send a structured weekly report email

## Core Principles

- Supabase/PostgreSQL is canonical storage
- Notion is a sync and review layer
- source-specific parsers are required
- official Canadian sources outrank trade sources
- unknown fields render as `Unknown`, never blank
- IMDb matching must support manual review and safe fallbacks

## Main Commands

- `film-agent init-db`
- `film-agent setup-notion`
- `film-agent ingest-imdb`
- `film-agent ingest-sources`
- `film-agent run-weekly --dry-run`

## Runtime

- Python 3.11+
- Supabase
- Notion
- Resend
- GitHub Actions
