from film_intelligence_agent.parsers.sources.cmf import CMFParser
from film_intelligence_agent.parsers.sources.creative_bc import CreativeBCParser
from film_intelligence_agent.parsers.sources.nfb import NFBNewsParser
from film_intelligence_agent.parsers.sources.ontario_creates import OntarioCreatesParser
from film_intelligence_agent.parsers.sources.playback import PlaybackParser
from film_intelligence_agent.parsers.sources.telefilm import TelefilmParser


SOURCE_META = {
    "name": "Test Source",
    "url": "https://example.com",
    "tier": "tier_0_canada_official",
    "source_type": "canada_official_funder",
}


def test_telefilm_parser_only_uses_structured_table_rows() -> None:
    html = """
    <html>
      <body>
        <h2>Funded Projects</h2>
        <table>
          <tr><th>Title</th><th>Program</th></tr>
          <tr><td>Dark Harvest</td><td>Production</td></tr>
        </table>
      </body>
    </html>
    """
    films = TelefilmParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["Dark Harvest"]


def test_cmf_parser_requires_title_and_funding_signal() -> None:
    html = """
    <html>
      <body>
        <p>Search for funded projects</p>
        <p>Export Results (XLSX)</p>
        <p>Reports</p>
        <p>The Silent Shore Production North Shore Films</p>
        <p>Fiscal Year</p><p>2025 - 2026</p>
        <p>Content Type</p><p>Feature Film</p>
        <p>Commitment</p><p>$400000.00</p>
        <p>Activity</p><p>Production</p>
        <p>Region</p><p>Toronto</p>
        <p>Program</p><p>Regional Production Funding</p>
      </body>
    </html>
    """
    films = CMFParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["The Silent Shore"]
    assert films[0].production_company == "North Shore Films"
    assert films[0].project_type == "feature_film"


def test_cmf_parser_skips_games_and_interactive_projects() -> None:
    html = """
    <html>
      <body>
        <p>Search for funded projects</p>
        <p>Export Results (XLSX)</p>
        <p>Tax Credit Updates</p>
        <p>Fiscal Year</p><p>2025 - 2026</p>
        <p>Content Type</p><p>Game</p>
        <p>Activity</p><p>Production</p>
        <p>Program</p><p>Commercial Projects Program</p>
      </body>
    </html>
    """
    assert CMFParser().parse(html, SOURCE_META) == []


def test_cmf_parser_accepts_series_projects() -> None:
    html = """
    <html>
      <body>
        <p>Search for funded projects</p>
        <p>Export Results (XLSX)</p>
        <p>North Shore Production Bright Harbor Media</p>
        <p>Fiscal Year</p><p>2025 - 2026</p>
        <p>Content Type</p><p>Drama Series</p>
        <p>Commitment</p><p>$900000.00</p>
        <p>Activity</p><p>Production</p>
        <p>Region</p><p>Vancouver</p>
        <p>Program</p><p>Broadcaster Envelope</p>
      </body>
    </html>
    """
    films = CMFParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["North Shore"]
    assert films[0].project_type == "series"


def test_creative_bc_parser_skips_rows_without_metadata() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><td>Tax Credit Updates</td></tr>
          <tr><td>Dark Harvest</td><td>Vancouver</td><td>In Production</td></tr>
        </table>
      </body>
    </html>
    """
    films = CreativeBCParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["Dark Harvest"]


def test_playback_parser_requires_project_signal() -> None:
    html = """
    <html>
      <body>
        <article><h2>Dark Harvest</h2><p>Interview with the composer</p></article>
        <article><h2>The Silent Shore</h2><p>Feature film begins shooting in Ontario</p></article>
      </body>
    </html>
    """
    films = PlaybackParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["The Silent Shore"]


def test_ontario_creates_program_page_emits_no_project_records() -> None:
    html = "<html><body><h1>Linear Content Stream</h1><p>Funding available</p></body></html>"
    assert OntarioCreatesParser().parse(html, SOURCE_META) == []


def test_nfb_news_parser_requires_production_signal() -> None:
    html = """
    <html>
      <body>
        <article><h2>NFB announces documentary feature in production</h2><p>New film enters production this spring.</p></article>
        <article><h2>Annual reports</h2><p>Browse our archive.</p></article>
      </body>
    </html>
    """
    films = NFBNewsParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["NFB announces documentary feature in production"]
