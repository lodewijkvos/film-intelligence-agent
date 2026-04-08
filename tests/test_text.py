from film_intel_agent.utils.text import normalize_name, normalize_title


def test_normalize_title_strips_articles_and_punctuation():
    assert normalize_title("The Working Title: Example!") == "example"


def test_normalize_name_collapses_spaces():
    assert normalize_name("Lodewijk   Vos") == "lodewijk vos"
