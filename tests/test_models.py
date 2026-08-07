from datetime import date

from pa_digest.models import Article, fallback_article_id, normalize_doi


def test_normalize_doi_variants() -> None:
    assert normalize_doi("HTTPS://DOI.ORG/10.1234/ABC.1 ") == "10.1234/abc.1"
    assert normalize_doi("doi: 10.1234/ABC.1.") == "10.1234/abc.1"
    assert normalize_doi(None) is None


def test_article_id_prefers_doi() -> None:
    article = Article(
        doi="https://doi.org/10.1234/ABC",
        title="A Study",
        journal="Public Administration",
        journal_short="PA",
        publication_date=date(2026, 8, 7),
        url="https://doi.org/10.1234/abc",
    )
    assert article.stable_id == "doi:10.1234/abc"


def test_fallback_id_is_normalized_and_deterministic() -> None:
    first = fallback_article_id("Journal", "  A   Study ", date(2026, 8, 7))
    second = fallback_article_id("journal", "a study", date(2026, 8, 7))
    assert first == second
    assert first.startswith("hash:")

