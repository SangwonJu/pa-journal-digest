from __future__ import annotations

import json
import os

import httpx
from openai import OpenAI

from .models import Article


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary_ko": {"type": "string"},
        "topic_area": {
            "type": "string",
            "enum": [
                "조직·인사",
                "재무·예산",
                "정책과정",
                "공공관리·성과",
                "거버넌스·협력",
                "디지털정부",
                "시민·민주성",
                "지방·도시",
                "비영리",
                "행정이론·윤리",
                "분야 미상",
            ],
        },
        "method": {
            "type": "string",
            "enum": [
                "서베이",
                "실험",
                "준실험",
                "질적연구",
                "혼합방법론",
                "이론/개념",
                "방법 미상",
            ],
        },
        "method_detail": {
            "type": "string",
            "maxLength": 30,
        },
        "constructs": {
            "type": "array",
            "items": {"type": "string", "maxLength": 40},
            "minItems": 1,
            "maxItems": 2,
        },
        "ai_related": {"type": "boolean"},
    },
    "required": ["summary_ko", "topic_area", "method", "method_detail", "constructs", "ai_related"],
    "additionalProperties": False,
}


class ArticleSummarizer:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-6-luna")

    def summarize(self, article: Article) -> None:
        if article.abstract:
            source = f"English abstract:\n{article.abstract}"
            instruction = (
                "Write a faithful Korean summary in one or two concise sentences. "
                "State the research question, approach, and principal finding only when the abstract supports them. "
                "Do not add facts, evaluation, or background knowledge. Classify one primary topic area and one "
                "research method using exactly one schema label. Use Survey only when survey data are explicit. "
                "Use Theory/Concept for theoretical, conceptual, or review articles. In method_detail, give the "
                "specific design or analytic approach in two or three short Korean words (examples: 패널 설문, "
                "설문 실험, 이중차분, 심층 인터뷰, 순차 혼합, 개념적 모형). Do not repeat the broad method label. "
                "Extract one or two canonical constructs or theories. Each array item must contain exactly one "
                "distinct concept in one to three English words (for example PSM, bureaucracy, governance, policy "
                "diffusion, or political market framework). Never combine two concepts in one item. Preserve common "
                "acronyms and use consistent title case for multiword terms. Do not use generic words such as public "
                "administration or study. Use performance only when it is itself the focal theoretical construct. "
                + AI_RELATED_RULE
                + KOREAN_STYLE_RULES
            )
            article.summary_basis = "abstract"
        else:
            source = "No abstract is available."
            instruction = (
                "Write exactly one short Korean sentence describing only the apparent topic from the title. "
                "Begin with '제목 기준:' and do not claim any method, evidence, or finding. Infer only the primary "
                "topic and one or two constructs that are explicit in the title. Set method to '방법 미상' and "
                "method_detail to an empty string. "
                + AI_RELATED_RULE
                + KOREAN_STYLE_RULES
            )
            article.summary_basis = "title"
        prompt = (
            f"Journal: {article.journal}\n"
            f"Title: {article.title}\n"
            f"{source}\n\n"
            f"{instruction}"
        )
        response = self.client.responses.create(
            model=self.model,
            reasoning={"effort": "none"},
            input=[
                {
                    "role": "system",
                    "content": (
                        "You summarize peer-reviewed public administration research for a Korean scholar. "
                        "Return valid JSON matching the supplied schema. Preserve nuance and uncertainty."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "article_summary",
                    "strict": True,
                    "schema": SUMMARY_SCHEMA,
                }
            },
        )
        parsed = json.loads(response.output_text)
        summary = " ".join(parsed["summary_ko"].split())
        if not summary:
            raise RuntimeError(f"OpenAI returned an empty summary for {article.stable_id}")
        article.summary_ko = summary
        article.topic_area = parsed["topic_area"]
        article.method = parsed["method"]
        article.method_detail = " ".join(parsed["method_detail"].split()) or None
        article.constructs = [" ".join(item.split()) for item in parsed["constructs"] if item.strip()][:2]
        # Papers kept by the broad-journal AI screen stay flagged even if this call says otherwise.
        article.ai_related = article.ai_related or bool(parsed.get("ai_related", False))


    def select_ai_social(self, articles: list[Article]) -> list[Article]:
        """Keep only articles whose subject is AI as it bears on politics or psychology.

        Used for broad journals (NHB, PNAS, Science, Nature). Candidates are judged in batches on title
        and abstract, so one call covers a whole week of PNAS.
        """
        kept: list[Article] = []
        for start in range(0, len(articles), AI_FILTER_BATCH):
            chunk = articles[start : start + AI_FILTER_BATCH]
            listing = "\n\n".join(
                f"[{index}] {article.title}\n{article.abstract or '(no abstract)'}"
                for index, article in enumerate(chunk)
            )
            response = self.client.responses.create(
                model=self.model,
                reasoning={"effort": "none"},
                input=[
                    {"role": "system", "content": AI_FILTER_INSTRUCTIONS},
                    {"role": "user", "content": listing},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ai_social_selection",
                        "strict": True,
                        "schema": AI_FILTER_SCHEMA,
                    }
                },
            )
            selected = set(json.loads(response.output_text)["relevant"])
            for index, article in enumerate(chunk):
                if index in selected:
                    article.ai_related = True
                    kept.append(article)
        return kept


# Style rules for summary_ko, drawn from Korean humanizer guides (IsaacEryn/humanizer-ko,
# dandacompany/dante-skills humanize-korean, hjongc/humanizer-kr) and narrowed to
# one- or two-sentence formal summaries of academic abstracts.
KOREAN_STYLE_RULES = (
    " Write summary_ko the way a Korean scholar jots a note for colleagues: plain written register, "
    "one consistent ending (~했다, ~나타났다), never mixing in ~함 or ~습니다. "
    "Content: what was examined, with what data or design, and the one or two main results; add an "
    "implication only if the abstract states one. Keep the abstract's concrete terms, samples, settings "
    "and numbers, and keep technical terms and acronyms as written. Do not strengthen, weaken or "
    "generalize a claim beyond the abstract's scope. "
    "Avoid translationese: no double passive (검증되어졌다 -> 검증했다), no '~에 의해' agent phrases "
    "(A에 의해 제안된 -> A가 제안한), no '~에 있어서', no '~라고 할 수 있다', no comparative '보다 ~한' "
    "without a stated comparison, no '해당'/'그것' as filler subjects. "
    "Prefer verbs to nominalized predicates (향상을 가능하게 함 -> 향상시켰다), and plain predicates to "
    "inflated ones (~로 자리잡고 있다, 심화되고 있다). "
    "Do not use empty intensifiers or stock words: 획기적, 혁신적, 매우 중요한, 핵심적인 역할, 다양한, "
    "심층적, 다각적, 포괄적, 시너지, 필요성이 대두되고 있다, 이론적·실무적 시사점. "
    "Do not stack hedges (~일 수 있을 것으로 보인다 -> ~일 수 있다). "
    "Do not open with '본 연구는' or '이 연구는'; begin with what was examined. Do not close with "
    "'~에 기여할 것으로 기대된다', '~할 것이다' or other formulaic positive endings. "
    "No connective chains (이를 통해, 나아가, 아울러), no '~뿐만 아니라 ~도', no '단순한 X가 아니라 Y', "
    "no lists of three unless the abstract measured three things, no dashes, and no colon except the "
    "required '제목 기준:'. Keep each sentence to one clear point."
)
AI_RELATED_RULE = (
    "Set ai_related to true only when artificial intelligence itself (large language models, chatbots, "
    "generative AI, algorithms or algorithmic decision-making, recommender systems, automation by AI) is a "
    "central subject of the article, for example how people, governments or organizations use, trust, "
    "regulate or are affected by AI. Set it to false when machine learning is only a measurement or "
    "analysis tool for a question that is not about AI."
)
AI_FILTER_BATCH = 40
AI_FILTER_SCHEMA = {
    "type": "object",
    "properties": {"relevant": {"type": "array", "items": {"type": "integer"}}},
    "required": ["relevant"],
    "additionalProperties": False,
}
AI_FILTER_INSTRUCTIONS = (
    "You screen new articles from broad science journals for a political scientist and public "
    "administration scholar who studies how people interact with AI. Return the indices of articles "
    "whose central subject is AI (large language models, chatbots, generative AI, algorithms, "
    "recommender systems, automated decision-making) AND whose question concerns politics, government, "
    "public opinion, persuasion, beliefs, misinformation, trust, moral or social judgment, or human "
    "psychology and behaviour.\n\n"
    "Typical articles to keep:\n"
    "- Costello, Pennycook and Rand: conversations with an LLM durably reduce belief in conspiracy "
    "theories.\n"
    "- Myra Cheng and colleagues: sycophantic LLMs affirm users, and this shapes users' judgments, "
    "prosocial intentions and reliance on AI.\n"
    "- AI-written political messages persuading voters; LLMs simulating survey respondents; public "
    "attitudes toward AI in government; AI and political polarization or misinformation.\n\n"
    "Exclude news stories, editorials, letters, obituaries and book reviews. Exclude articles that only use machine learning as a measurement or prediction tool for a "
    "question that is not about AI, and AI work in biology, medicine, chemistry, physics, materials "
    "or climate science. When unsure, exclude. Return an empty list when nothing qualifies."
)


class ResendMailer:
    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY")
        if not self.api_key:
            raise RuntimeError("RESEND_API_KEY is required")
        self.timeout = timeout

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        html: str,
        text: str,
        idempotency_key: str,
    ) -> str:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
            json={
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        email_id = response.json().get("id")
        if not email_id:
            raise RuntimeError("Resend accepted the request but returned no email id")
        return str(email_id)
