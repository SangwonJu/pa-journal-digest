import json
from datetime import date
from types import SimpleNamespace

from pa_digest.models import Article
from pa_digest.services import SUMMARY_SCHEMA, ArticleSummarizer


def test_summarizer_assigns_summary_and_research_tags() -> None:
    assert "이론/개념" in SUMMARY_SCHEMA["properties"]["method"]["enum"]
    assert "ai_related" in SUMMARY_SCHEMA["required"]
    summarizer = ArticleSummarizer(api_key="test")
    payload = {
        "summary_ko": "공공봉사동기와 성과의 관계를 분석한다.",
        "topic_area": "조직·인사",
        "method": "서베이",
        "method_detail": "패널 설문",
        "constructs": [" PSM ", "Public service performance"],
        "ai_related": False,
        "is_editorial": True,
    }
    prompts = []

    def create(**kwargs):
        prompts.append(kwargs["input"][1]["content"])
        return SimpleNamespace(output_text=json.dumps(payload))

    summarizer.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    article = Article(
        title="Public Service Motivation and Performance",
        journal="Public Administration Review",
        journal_short="PAR",
        publication_date=date(2026, 8, 7),
        url="https://example.test/article",
        abstract="We examine the relationship using a longitudinal survey.",
    )

    summarizer.summarize(article)
    assert "본 연구는" in prompts[0] and "검증되어졌다" in prompts[0]
    assert "is_editorial" in prompts[0]
    assert article.is_editorial is True

    assert article.summary_ko == payload["summary_ko"]
    assert article.topic_area == "조직·인사"
    assert article.method == "서베이"
    assert article.method_detail == "패널 설문"
    assert article.constructs == ["PSM", "Public service performance"]
    assert article.summary_basis == "abstract"


def test_select_ai_social_keeps_only_indices_the_model_returns() -> None:
    summarizer = ArticleSummarizer(api_key="test")
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps({"relevant": [1]}))

    summarizer.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    articles = [
        Article(
            title=title,
            journal="Proceedings of the National Academy of Sciences",
            journal_short="PNAS",
            publication_date=date(2026, 11, 5),
            url=f"https://example.test/{index}",
            abstract=abstract,
        )
        for index, (title, abstract) in enumerate(
            [
                ("Deep learning predicts protein folding", "We train a network on structures."),
                ("Dialogues with AI reduce conspiracy beliefs", "Participants conversed with an LLM."),
            ]
        )
    ]

    kept = summarizer.select_ai_social(articles)

    assert [article.title for article in kept] == ["Dialogues with AI reduce conspiracy beliefs"]
    assert kept[0].ai_related is True
    assert articles[0].ai_related is False
    assert len(calls) == 1
    assert "Costello" in calls[0]["input"][0]["content"]
    assert "[1] Dialogues with AI reduce conspiracy beliefs" in calls[0]["input"][1]["content"]
