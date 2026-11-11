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
    assert "Malgun Gothic" in html
    assert "Helvetica" in html
    assert "Georgia" not in html
    assert "background:#e9edf1" in html
    assert "background:#ffffff" in html
    assert "#f6f4ef" not in html
    assert "border-left" not in html
    assert "border:1px solid #1f5f8b" in html
    assert "text-transform:uppercase" not in html
    assert "text-align:justify" not in html
    assert ">시민·민주성</b>" in html
    assert ">서베이 (패널 설문)</b>" in html
    assert ">Bureaucracy</b>" in html
    assert "<span" not in html
    assert "white-space:nowrap" in html
    assert "https://doi.org/10.1234/example" in html
    assert "-ms-text-size-adjust:100%" in html
    assert '<table role="presentation"' in html
    assert 'width="900"' in html
    assert "max-width:900px" in html
    assert "2026년 8월 7일 금요일" in html
    assert "행정·정책 <b>1</b>편" in html
    assert 'href="#field-' not in html
    assert "display:inline-block" not in html
    assert "누적 논문 정리표 다운로드 (XLSX)" in html
    assert "PA_Journal_Digest_Archive.xlsx" in text


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
    assert "Tier 1, 1편" in html
    assert "Tier 2, 1편" in html


def test_render_empty_digest_includes_daily_confirmation() -> None:
    subject, html, text = render_newsletter([], date(2026, 8, 8))

    assert "신규 0편" in subject
    assert "오늘은 새로 확인된 논문이 없습니다." in html
    assert "오늘은 새로 확인된 논문이 없습니다." in text
    assert "max-width:900px" in html
    assert "43개 저널을 모두 확인했습니다." in html


def test_render_groups_sections_by_field() -> None:
    def make(journal: str, short: str) -> Article:
        return Article(
            title=f"A {short} Article",
            journal=journal,
            journal_short=short,
            publication_date=date(2026, 8, 5),
            url=f"https://example.test/{short}",
            summary_ko="요약",
        )

    articles = [
        make("Strategic Management Journal", "SMJ"),
        make("Political Behavior", "PolBeh"),
        make("Governance", "Governance"),
        make("Journal of Personality and Social Psychology", "JPSP"),
    ]
    _, html, text = render_newsletter(articles, date(2026, 8, 7))

    fields = ["행정·정책", "정치학", "경영·조직", "심리학"]
    positions = [html.index(f">{field}</td>") for field in fields]
    assert positions == sorted(positions)
    assert "정보시스템" not in html
    assert text.index("■ 행정·정책") < text.index("■ 심리학")


def test_render_marks_ai_related_papers() -> None:
    def make(title: str, ai: bool) -> Article:
        return Article(
            title=title,
            journal="Political Behavior",
            journal_short="PolBeh",
            publication_date=date(2026, 8, 5),
            url=f"https://example.test/{title}",
            abstract="An abstract.",
            summary_ko="요약",
            ai_related=ai,
        )

    _, html, text = render_newsletter([make("LLM persuasion", True), make("Turnout", False)], date(2026, 8, 7))

    assert html.count(">🤖 AI</b>&nbsp;") == 1
    assert "🤖 AI 1편" in html
    assert "[🤖 AI] 한국어 요약" in text
    assert "border:1px solid #8c3a5b;background:#f5e8ee" in html
    assert "border:3px solid" not in html
