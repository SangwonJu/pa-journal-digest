from datetime import date

from pa_digest.models import Article
from pa_digest.render import render_newsletter


def test_render_includes_escaped_content_and_fallback_notice() -> None:
    article = Article(
        doi="10.1234/example",
        title="Trust & <Government>",
        journal="Governance",
        journal_short="Governance",
        authors=["Jane Doe"],
        author_affiliations={"Jane Doe": ["Example University"]},
        publication_date=date(2026, 8, 5),
        url="https://doi.org/10.1234/example?a=1&b=2",
        summary_ko="제목 기준: 정부 신뢰를 다룬다.",
        summary_basis="title",
    )
    subject, html, text = render_newsletter([article], date(2026, 8, 7))
    assert "신규 1편" in subject
    assert "Trust &amp; &lt;Government&gt;" in html
    assert "Abstract unavailable" in html
    assert "제목 기준" in text
    assert "Example University" in html
    assert "Times New Roman" in html
    assert "text-align:justify" in html
    assert "https://doi.org/10.1234/example" in html
    assert "-ms-text-size-adjust:100%" in html
    assert '<table role="presentation"' in html
    assert 'width="640"' in html
    assert "max-width:640px" in html


def test_render_contains_english_abstract() -> None:
    article = Article(
        title="A Study",
        journal="Public Administration",
        journal_short="PA",
        publication_date=date(2026, 8, 5),
        url="https://example.test",
        abstract="This study tests an argument.",
        summary_ko="이 연구는 주장을 검증한다.",
    )
    _, html, text = render_newsletter([article], date(2026, 8, 7))
    assert "This study tests an argument." in html
    assert "English abstract" in text


def test_render_orders_journals_by_field_rank() -> None:
    lower_ranked = Article(
        title="An ARPA Article",
        journal="The American Review of Public Administration",
        journal_short="ARPA",
        publication_date=date(2026, 8, 5),
        url="https://example.test/arpa",
        summary_ko="요약",
    )
    higher_ranked = Article(
        title="A JPART Article",
        journal="Journal of Public Administration Research and Theory",
        journal_short="JPART",
        publication_date=date(2026, 8, 5),
        url="https://example.test/jpart",
        summary_ko="요약",
    )
    _, html, text = render_newsletter([lower_ranked, higher_ranked], date(2026, 8, 7))
    assert html.index("Journal of Public Administration Research and Theory") < html.index(
        "The American Review of Public Administration"
    )
    assert text.index("Journal of Public Administration Research and Theory") < text.index(
        "The American Review of Public Administration"
    )
    assert "Tier 1" in html
    assert "Tier 2" in html
