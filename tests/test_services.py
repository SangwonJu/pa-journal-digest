import json
from datetime import date
from types import SimpleNamespace

from pa_digest.models import Article
from pa_digest.services import SUMMARY_SCHEMA, ArticleSummarizer


def test_summarizer_assigns_summary_and_research_tags() -> None:
    assert "이론/개념" in SUMMARY_SCHEMA["properties"]["method"]["enum"]
    summarizer = ArticleSummarizer(api_key="test")
    payload = {
        "summary_ko": "공공봉사동기와 성과의 관계를 분석한다.",
        "topic_area": "조직·인사",
        "method": "서베이",
        "method_detail": "패널 설문",
        "constructs": [" PSM ", "Public service performance"],
    }
    summarizer.client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **_: SimpleNamespace(output_text=json.dumps(payload)))
    )
    article = Article(
        title="Public Service Motivation and Performance",
        journal="Public Administration Review",
        journal_short="PAR",
        publication_date=date(2026, 8, 7),
        url="https://example.test/article",
        abstract="We examine the relationship using a longitudinal survey.",
    )

    summarizer.summarize(article)

    assert article.summary_ko == payload["summary_ko"]
    assert article.topic_area == "조직·인사"
    assert article.method == "서베이"
    assert article.method_detail == "패널 설문"
    assert article.constructs == ["PSM", "Public service performance"]
    assert article.summary_basis == "abstract"
