from datetime import date

from pa_digest.sources import clean_markup, is_scholarly_article, publication_date


def test_clean_crossref_jats_abstract() -> None:
    value = "<jats:p>This &amp; that <jats:bold>result</jats:bold>.</jats:p>"
    assert clean_markup(value) == "This & that result ."


def test_content_filter() -> None:
    assert is_scholarly_article("Administrative Burden and Trust")
    assert is_scholarly_article("A Systematic Review of Public Value")
    assert not is_scholarly_article("Book Review: Public Management Today")
    assert not is_scholarly_article("Correction: Administrative Burden and Trust")
    assert not is_scholarly_article("Editor's Introduction: A Special Issue")


def test_publication_date_prefers_online() -> None:
    message = {
        "published-online": {"date-parts": [[2026, 8, 2]]},
        "published-print": {"date-parts": [[2027, 1]]},
    }
    assert publication_date(message) == date(2026, 8, 2)

