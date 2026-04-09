from film_intelligence_agent.parsers.sources.cmf import CMFParser
from film_intelligence_agent.parsers.sources.creative_bc import CreativeBCParser
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
        <article><h2>Reports</h2><p>Reports and statistics</p></article>
        <article><h2>The Silent Shore</h2><p>Funded project in production</p></article>
      </body>
    </html>
    """
    films = CMFParser().parse(html, SOURCE_META)
    assert [film.title for film in films] == ["The Silent Shore"]


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
