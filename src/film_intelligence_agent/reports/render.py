from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from jinja2 import Template
from sqlalchemy import desc, select

from film_intelligence_agent.db.models import Collaborator, Company, Film, FilmCompany, FilmPerson, Person
from film_intelligence_agent.db.session import db_session


SECTION_ORDER = (
    "Top Opportunities",
    "Newly Funded Canadian Projects (Early Opportunities)",
    "Canada Greenlights",
    "Horror < $10M (North America / Europe)",
    "Collaborator Matches",
    "Needs Review",
    "Weekly Summary",
)

SECTION_EMPTY_STATES = {
    "Top Opportunities": "No high-confidence opportunities made the cut for this run.",
    "Newly Funded Canadian Projects (Early Opportunities)": "No funded Canadian film or series projects were captured in this run.",
    "Canada Greenlights": "No Canadian greenlights or active productions were captured in this run.",
    "Horror < $10M (North America / Europe)": "No horror projects in the target budget/region band were captured in this run.",
    "Collaborator Matches": "No direct collaborator or warm-path matches are available yet.",
    "Needs Review": "No low-confidence items are waiting for review right now.",
    "Weekly Summary": "",
}


@dataclass(slots=True)
class RenderedReport:
    summary: str
    html: str
    text: str
    sections: dict[str, list["ProjectCard"]]
    stats: dict[str, int]
    lookback_days: int


@dataclass(slots=True)
class ProjectCard:
    film_id: str
    title: str
    title_url: str | None
    status: str
    budget: str
    country: str
    region: str
    production_company: str
    production_company_url: str | None
    director: str
    director_url: str | None
    director_note: str | None
    editor: str
    editor_url: str | None
    editor_note: str | None
    composer: str
    composer_url: str | None
    composer_note: str | None
    producers: str
    producer_links: list[tuple[str, str | None]]
    producer_notes: dict[str, str]
    source_name: str
    source_url: str
    opportunity_score: int
    data_confidence_score: int
    genre: str | None
    why_this_matters: str
    recent_sources: list[tuple[str, str | None]]


TEMPLATE = Template(
    """
    <html>
      <body style="margin:0;padding:0;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#111111;">
        <div style="max-width:860px;margin:0 auto;padding:28px 24px 48px;">
          <div style="font-size:24px;font-weight:800;margin-bottom:6px;">🎬 Weekly Film Intelligence Report</div>
          <div style="font-size:14px;color:#444444;margin-bottom:18px;">{{ report_label }}</div>
          <div style="border-top:1px solid #dddddd;margin:0 0 24px;"></div>

          {% for section_name in section_order %}
            <div style="margin:0 0 26px;">
              <h2 style="margin:0 0 14px;font-size:22px;">{{ section_icons.get(section_name, "•") }} {{ section_name }}</h2>
              {% if section_name == "Weekly Summary" %}
                <ul style="margin:0;padding-left:20px;line-height:1.8;">
                  <li>Lookback window: {{ lookback_days }} days</li>
                  <li>Total qualified projects mirrored this run: {{ stats["Projects Included"] }}</li>
                  <li>Canadian funded/greenlit projects: {{ stats["Canada Signals"] }}</li>
                  <li>Needs review items: {{ stats["Needs Review"] }}</li>
                </ul>
              {% elif sections[section_name] %}
                {% for film in sections[section_name] %}
                  <div style="margin:0 0 18px;">
                    <div style="font-size:18px;font-weight:700;margin-bottom:8px;">
                      {% if film.title_url %}
                        <a href="{{ film.title_url }}" style="color:#111111;text-decoration:underline;">{{ film.title }}</a>
                      {% else %}
                        {{ film.title }}
                      {% endif %}
                    </div>
                    <ul style="margin:0;padding-left:22px;line-height:1.8;">
                      <li><strong>Budget:</strong> {{ film.budget }}</li>
                      <li><strong>Country:</strong> {{ film.country }}</li>
                      <li><strong>Region:</strong> {{ film.region }}</li>
                      <li><strong>Production Company:</strong>
                        {% if film.production_company_url %}
                          <a href="{{ film.production_company_url }}" style="color:#111111;">{{ film.production_company }}</a>
                        {% else %}
                          {{ film.production_company }}
                        {% endif %}
                      </li>
                      <li><strong>Director:</strong>
                        {% if film.director_url %}
                          <a href="{{ film.director_url }}" style="color:#111111;">{{ film.director }}</a>
                        {% else %}
                          {{ film.director }}
                        {% endif %}
                        {% if film.director_note %}<em> {{ film.director_note }}</em>{% endif %}
                      </li>
                      <li><strong>Editor:</strong>
                        {% if film.editor_url %}
                          <a href="{{ film.editor_url }}" style="color:#111111;">{{ film.editor }}</a>
                        {% else %}
                          {{ film.editor }}
                        {% endif %}
                        {% if film.editor_note %}<em> {{ film.editor_note }}</em>{% endif %}
                      </li>
                      <li><strong>Composer:</strong>
                        {% if film.composer_url %}
                          <a href="{{ film.composer_url }}" style="color:#111111;">{{ film.composer }}</a>
                        {% else %}
                          {{ film.composer }}
                        {% endif %}
                        {% if film.composer_note %}<em> {{ film.composer_note }}</em>{% endif %}
                      </li>
                      <li><strong>Producers:</strong>
                        <ul style="margin:4px 0 0;padding-left:20px;">
                          {% if film.producer_links %}
                            {% for producer_name, producer_url in film.producer_links %}
                              <li>
                                {% if producer_url %}
                                  <a href="{{ producer_url }}" style="color:#111111;">{{ producer_name }}</a>
                                {% else %}
                                  {{ producer_name }}
                                {% endif %}
                                {% if film.producer_notes.get(producer_name) %}<em> {{ film.producer_notes.get(producer_name) }}</em>{% endif %}
                              </li>
                            {% endfor %}
                          {% else %}
                            <li>Unknown</li>
                          {% endif %}
                        </ul>
                      </li>
                      <li><strong>Status:</strong> {{ film.status }}</li>
                      <li><strong>Opportunity Score:</strong> {{ film.opportunity_score }}</li>
                      <li><strong>Why this matters:</strong> {{ film.why_this_matters }}</li>
                      <li><strong>Recent Press / Sources:</strong>
                        <ul style="margin:4px 0 0;padding-left:20px;">
                          {% if film.recent_sources %}
                            {% for source_name, source_url in film.recent_sources %}
                              <li>
                                {% if source_url %}
                                  <a href="{{ source_url }}" style="color:#111111;">{{ source_name }}</a>
                                {% else %}
                                  {{ source_name }}
                                {% endif %}
                              </li>
                            {% endfor %}
                          {% else %}
                            <li>No recent sources attached yet.</li>
                          {% endif %}
                        </ul>
                      </li>
                    </ul>
                  </div>
                  {% if not loop.last %}
                    <div style="border-top:1px solid #dddddd;margin:16px 0 18px;"></div>
                  {% endif %}
                {% endfor %}
              {% else %}
                <p style="margin:0;color:#555555;line-height:1.6;">{{ empty_states[section_name] }}</p>
              {% endif %}
            </div>
          {% endfor %}
        </div>
      </body>
    </html>
    """
)


class ReportRenderer:
    def render(self, lookback_days: int = 14) -> RenderedReport:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        report_label = f"Week of {datetime.utcnow().strftime('%B %-d, %Y')}"
        section_icons = {
            "Top Opportunities": "🎯",
            "Newly Funded Canadian Projects (Early Opportunities)": "🍁",
            "Canada Greenlights": "🇨🇦",
            "Horror < $10M (North America / Europe)": "🩸",
            "Collaborator Matches": "🤝",
            "Needs Review": "⚠️",
            "Weekly Summary": "📝",
        }
        with db_session() as session:
            films = list(
                session.scalars(
                    select(Film)
                    .where(Film.first_seen_at >= cutoff)
                    .order_by(desc(Film.opportunity_score), desc(Film.data_confidence_score), desc(Film.last_seen_at))
                    .limit(100)
                )
            )
            cards = [self._build_card(session, film) for film in films]

        sections: dict[str, list[ProjectCard]] = {name: [] for name in SECTION_ORDER}
        top_opportunities = [card for film, card in zip(films, cards, strict=False) if film.opportunity_score >= 40][:8]
        funded_canada = [card for film, card in zip(films, cards, strict=False) if film.country == "Canada" and film.status == "funded"][:8]
        canada_greenlights = [
            card for film, card in zip(films, cards, strict=False) if film.country == "Canada" and film.status in {"greenlit", "production"}
        ][:8]
        horror_targets = [
            card
            for film, card in zip(films, cards, strict=False)
            if film.genre
            and "horror" in film.genre.lower()
            and (film.region in {"Canada", "North America", "Europe"} or film.country in {"Canada", "United States"})
        ][:8]
        collaborator_matches: list[ProjectCard] = []
        needs_review = [card for film, card in zip(films, cards, strict=False) if film.data_confidence_score < 70][:8]

        sections["Top Opportunities"] = top_opportunities
        sections["Newly Funded Canadian Projects (Early Opportunities)"] = funded_canada
        sections["Canada Greenlights"] = canada_greenlights
        sections["Horror < $10M (North America / Europe)"] = horror_targets
        sections["Collaborator Matches"] = collaborator_matches
        sections["Needs Review"] = needs_review
        sections["Weekly Summary"] = []

        stats = {
            "Projects Included": len(films),
            "Top Opportunities": len(top_opportunities),
            "Canada Signals": len({card.film_id for card in funded_canada + canada_greenlights}),
            "Needs Review": len(needs_review),
        }
        summary = f"{len(films)} qualified film and series projects in the current report window."

        text_lines = [
            "Weekly Film Intelligence Report",
            report_label,
            "",
            summary,
            "",
        ]
        for section_name in SECTION_ORDER:
            text_lines.append(f"{section_icons.get(section_name, '-')} {section_name}")
            if section_name == "Weekly Summary":
                text_lines.extend(
                    [
                        f"- Lookback window: {lookback_days} days",
                        f"- Projects included: {stats['Projects Included']}",
                        f"- Canada signals: {stats['Canada Signals']}",
                        f"- Needs review: {stats['Needs Review']}",
                    ]
                )
            elif sections[section_name]:
                for film in sections[section_name]:
                    text_lines.extend(
                        [
                            film.title,
                            f"  Country: {film.country}",
                            f"  Region: {film.region}",
                            f"  Budget: {film.budget}",
                            f"  Production Company: {film.production_company}",
                            f"  Director: {film.director}",
                            f"  Editor: {film.editor}",
                            f"  Composer: {film.composer}",
                            f"  Producers: {film.producers}",
                            f"  Status: {film.status}",
                            f"  Opportunity Score: {film.opportunity_score}",
                            f"  Why this matters: {film.why_this_matters}",
                            f"  IMDb: {film.title_url or 'Unknown'}",
                            f"  Source: {film.source_name} ({film.source_url})",
                        ]
                    )
                    if film.recent_sources:
                        text_lines.append("  Recent Press / Sources:")
                        for source_name, source_url in film.recent_sources:
                            text_lines.append(f"    - {source_name} ({source_url or 'Unknown'})")
                    else:
                        text_lines.append("  Recent Press / Sources: No recent sources attached yet.")
            else:
                text_lines.append(f"- {SECTION_EMPTY_STATES[section_name]}")
            text_lines.append("")

        html = TEMPLATE.render(
            summary=summary,
            report_label=report_label,
            sections=sections,
            section_order=SECTION_ORDER,
            section_icons=section_icons,
            empty_states=SECTION_EMPTY_STATES,
            stats=stats,
            lookback_days=lookback_days,
        )
        return RenderedReport(
            summary=summary,
            html=html,
            text="\n".join(text_lines).strip(),
            sections=sections,
            stats=stats,
            lookback_days=lookback_days,
        )

    def _build_card(self, session, film: Film) -> ProjectCard:
        people_rows = session.execute(
            select(
                FilmPerson.role,
                Person.full_name,
                Person.imdb_url,
                Person.is_known_collaborator,
                Collaborator.shared_project_names,
            )
            .join(Person, Person.id == FilmPerson.person_id)
            .outerjoin(Collaborator, Collaborator.person_id == Person.id)
            .where(FilmPerson.film_id == film.id)
            .order_by(FilmPerson.role, Person.full_name)
        ).all()
        company_rows = session.execute(
            select(FilmCompany.role, Company.name, Company.imdb_url)
            .join(Company, Company.id == FilmCompany.company_id)
            .where(FilmCompany.film_id == film.id)
            .order_by(FilmCompany.role, Company.name)
        ).all()

        def collaborator_note(is_known: bool, shared_projects: list[str] | None) -> str | None:
            if not is_known and not shared_projects:
                return None
            if shared_projects:
                sample = ", ".join(shared_projects[:2])
                extra = max(len(shared_projects) - 2, 0)
                suffix = f" +{extra} more" if extra else ""
                return f"(worked with you: {sample}{suffix})"
            return "(worked with you)"

        def first_person(*roles: str) -> tuple[str, str | None, str | None]:
            role_set = {role.lower() for role in roles}
            for role, full_name, imdb_url, is_known, shared_projects in people_rows:
                if (role or "").lower() in role_set:
                    return full_name, imdb_url, collaborator_note(bool(is_known), shared_projects)
            return "Unknown", None, None

        def collect_people(*roles: str) -> list[tuple[str, str | None, str | None]]:
            role_set = {role.lower() for role in roles}
            results: list[tuple[str, str | None, str | None]] = []
            seen: set[str] = set()
            for role, full_name, imdb_url, is_known, shared_projects in people_rows:
                if (role or "").lower() not in role_set:
                    continue
                key = full_name.lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append((full_name, imdb_url, collaborator_note(bool(is_known), shared_projects)))
            return results

        def first_company(*roles: str) -> tuple[str, str | None]:
            role_set = {role.lower() for role in roles}
            for role, name, imdb_url in company_rows:
                if (role or "").lower() in role_set:
                    return name, imdb_url
            return film.production_company or "Unknown", None

        director, director_url, director_note = first_person("director")
        editor, editor_url, editor_note = first_person("editor")
        composer, composer_url, composer_note = first_person("composer")
        producers = collect_people("producer", "executive producer")
        producer_label = ", ".join(name for name, _url, _note in producers) if producers else "Unknown"
        production_company, production_company_url = first_company("production_company", "producer", "studio")
        producer_notes = {name: note for name, _url, note in producers if note}
        why_bits = []
        if "canada" in (film.country or "").lower() or "canada" in (film.region or "").lower():
            why_bits.append("Canada-first signal")
        if film.status:
            why_bits.append(f"status is {film.status}")
        if producers and producer_notes:
            why_bits.append("known collaborator overlap on producing team")
        elif director_note or editor_note or composer_note:
            why_bits.append("known collaborator overlap on key creative team")
        if film.source_name:
            why_bits.append(f"source: {film.source_name}")
        why_this_matters = ". ".join(why_bits).capitalize() + "." if why_bits else "Needs manual review."
        recent_sources = [(film.source_name, film.source_url)] if film.source_name and film.source_url else []

        return ProjectCard(
            film_id=film.id,
            title=film.title,
            title_url=film.imdb_url,
            status=film.status or "Unknown",
            budget=film.budget_text or "Unknown",
            country=film.country or "Unknown",
            region=film.region or film.country or "Unknown",
            production_company=production_company,
            production_company_url=production_company_url,
            director=director,
            director_url=director_url,
            director_note=director_note,
            editor=editor,
            editor_url=editor_url,
            editor_note=editor_note,
            composer=composer,
            composer_url=composer_url,
            composer_note=composer_note,
            producers=producer_label,
            producer_links=[(name, url) for name, url, _note in producers],
            producer_notes=producer_notes,
            source_name=film.source_name,
            source_url=film.source_url,
            opportunity_score=film.opportunity_score,
            data_confidence_score=film.data_confidence_score,
            genre=film.genre,
            why_this_matters=why_this_matters,
            recent_sources=recent_sources,
        )
