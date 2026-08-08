from datetime import date

from pa_digest.models import Article
from pa_digest.sources import (
    apply_openalex_affiliations,
    author_details,
    clean_markup,
    is_scholarly_article,
    publisher_abstract_from_html,
    publisher_abstract_from_markdown,
    publication_date,
)


def test_clean_crossref_jats_abstract() -> None:
    value = "<jats:p>This &amp; that <jats:bold>result</jats:bold>.</jats:p>"
    assert clean_markup(value) == "This & that result ."


def test_content_filter() -> None:
    assert is_scholarly_article("Administrative Burden and Trust")
    assert is_scholarly_article("A Systematic Review of Public Value")
    assert not is_scholarly_article("Book Review: Public Management Today")
    assert not is_scholarly_article("Correction: Administrative Burden and Trust")
    assert not is_scholarly_article("Editor's Introduction: A Special Issue")
    assert not is_scholarly_article(
        "American Administrative Capacity By M. Joaquin, Springer, 2021. 213 pp. $97 (hardcover). ISBN: 123"
    )


def test_publisher_abstract_from_citation_meta() -> None:
    document = """
    <html><head>
      <meta name="citation_abstract" content="This study examines public service motivation using a preregistered survey experiment. The results show that institutional context moderates the treatment effect.">
    </head></html>
    """
    assert publisher_abstract_from_html(document, "Public Service Motivation") == (
        "This study examines public service motivation using a preregistered survey experiment. "
        "The results show that institutional context moderates the treatment effect."
    )


def test_publisher_abstract_from_scholarly_article_json_ld() -> None:
    document = """
    <script type="application/ld+json">
    {"@type":"ScholarlyArticle","description":"We analyze administrative burden with longitudinal data from three agencies. Results indicate that learning costs reduce program take-up among eligible residents."}
    </script>
    """
    assert publisher_abstract_from_html(document, "Administrative Burden") == (
        "We analyze administrative burden with longitudinal data from three agencies. "
        "Results indicate that learning costs reduce program take-up among eligible residents."
    )


def test_publisher_abstract_ignores_generic_or_short_descriptions() -> None:
    document = """
    <meta name="description" content="Publisher home page">
    <script type="application/ld+json">
    {"@type":"WebPage","description":"Browse journals and research from our publisher."}
    </script>
    """
    assert publisher_abstract_from_html(document, "A Research Article") is None


def test_publisher_abstract_from_reader_markdown() -> None:
    document = """
    ## ABSTRACT

    This study examines collaborative governance networks across several cities. Using a
    longitudinal network model, it finds that institutional similarity predicts durable ties.

    KEYWORDS:
    * governance
    * networks

    ## Disclosure statement
    None.
    """
    assert publisher_abstract_from_markdown(document, "Collaborative Governance") == (
        "This study examines collaborative governance networks across several cities. Using a "
        "longitudinal network model, it finds that institutional similarity predicts durable ties."
    )


def test_publisher_markdown_requires_abstract_heading() -> None:
    document = "A long publisher description that discusses subscriptions, journals, and access. " * 3
    assert publisher_abstract_from_markdown(document, "A Research Article") is None


def test_publication_date_prefers_online() -> None:
    message = {
        "published-online": {"date-parts": [[2026, 8, 2]]},
        "published-print": {"date-parts": [[2027, 1]]},
    }
    assert publication_date(message) == date(2026, 8, 2)


def test_author_details_include_deduplicated_affiliations() -> None:
    message = {
        "author": [
            {
                "given": "Jane",
                "family": "Doe",
                "affiliation": [
                    {"name": "School of Public Affairs, Example University"},
                    {"name": "School of Public Affairs, Example University"},
                ],
            },
            {"given": "John", "family": "Roe", "affiliation": []},
        ]
    }
    names, affiliations = author_details(message)
    assert names == ["Jane Doe", "John Roe"]
    assert affiliations == {"Jane Doe": ["School of Public Affairs, Example University"]}


def test_openalex_backfills_missing_affiliation() -> None:
    article = Article(
        title="A Study",
        journal="Governance",
        journal_short="Governance",
        authors=["Jane Doe", "John Roe"],
        publication_date=date(2026, 8, 7),
        url="https://example.test",
    )
    apply_openalex_affiliations(
        article,
        [
            {
                "author": {"display_name": "Jane Doe"},
                "institutions": [{"display_name": "Example University"}],
            }
        ],
    )
    assert article.author_affiliations == {"Jane Doe": ["Example University"]}
