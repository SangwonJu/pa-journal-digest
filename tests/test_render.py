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
        topic_area="시민·민주성",
        method="서베이",
        method_detail="패널 설문",
        constructs=["Trust", "Bureaucracy"],
    )
    subject, html, text = render_newsletter([article], date(2026, 8, 7))
    assert "신규 1편" in subject
    assert "Trust &amp; &lt;Government&gt;" in html
    assert "Abstract unavailable" in html
    assert "제목 기준" in text
    assert "Example University" in html
    assert "Times New Roman" in html
    assert "text-align:justify" not in html
    assert "font-size:15px" in html
    assert ">시민·민주성</strong>" in html
    assert ">서베이 (패널 설문)</strong>" in html
    assert ">Bureaucracy</strong>" in html
    assert ">분야</strong>" not in html
    assert ">방법</strong>" not in html
    assert ">개념</strong>" not in html
    assert "<span" not in html
    assert "white-space:nowrap" in html
    assert "2026-08-05 &nbsp;·&nbsp; Jane Doe" not in html
    assert "https://doi.org/10.1234/example" in html
    assert "-ms-text-size-adjust:100%" in html
    assert '<table role="presentation"' in html
    assert 'width="900"' in html
    assert "max-width:900px" in html
    assert "01" in html


def test_render_decodes_affiliation_entities_once() -> None:
    article = Article(
        title="A Study",
        journal="Public Administration Review",
        journal_short="PAR",
        authors=["Jane Doe"],
        author_affiliations={"Jane Doe": ["Policy &amp; Governance Lab"]},
        publication_date=date(2026, 8, 5),
        url="https://example.test",
        summary_ko="요약",
        topic_area="거버넌스·협력",
        method="이론/개념",
        method_detail="개념적 모형",
        constructs=["Governance"],
    )

    _, html, _ = render_newsletter([article], date(2026, 8, 7))

    assert "Policy &amp; Governance Lab" in html
    assert "Policy &amp;amp; Governance Lab" not in html


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
    assert ">Abstract</div>" in html


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
    assert "TIER 1" in html
    assert "TIER 2" in html


def test_render_empty_digest_includes_daily_confirmation() -> None:
    subject, html, text = render_newsletter([], date(2026, 8, 8))

    assert "신규 0편" in subject
    assert "오늘은 새로 확인된 논문이 없습니다." in html
    assert "오늘은 새로 확인된 논문이 없습니다." in text
    assert "max-width:900px" in html
