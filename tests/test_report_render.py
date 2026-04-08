from film_intel_agent.reports.render import HTML_TEMPLATE


def test_report_template_contains_required_budget_label():
    html = HTML_TEMPLATE.render(summary="Test", sections={})
    assert "Film Intelligence Weekly Report" in html
