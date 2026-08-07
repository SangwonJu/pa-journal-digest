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
                "현장실험",
                "설문실험",
                "실험(기타)",
                "준실험",
                "정량 관찰연구",
                "정성연구",
                "혼합방법",
                "비교·사례연구",
                "이론·개념연구",
                "문헌검토",
                "방법 미상",
            ],
        },
        "constructs": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 2,
        },
    },
    "required": ["summary_ko", "topic_area", "method", "constructs"],
    "additionalProperties": False,
}


class ArticleSummarizer:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    def summarize(self, article: Article) -> None:
        if article.abstract:
            source = f"English abstract:\n{article.abstract}"
            instruction = (
                "Write a faithful Korean summary in one or two concise sentences. "
                "State the research question, approach, and principal finding only when the abstract supports them. "
                "Do not add facts, evaluation, or background knowledge. Classify one primary topic area and one "
                "research method using the schema labels. Extract zero to two short, established constructs or "
                "theories (for example PSM, bureaucracy, governance, accountability), preserving common English "
                "terms or acronyms. Do not use generic words such as public administration, study, or performance "
                "as constructs unless performance is itself the focal theoretical construct."
            )
            article.summary_basis = "abstract"
        else:
            source = "No abstract is available."
            instruction = (
                "Write exactly one short Korean sentence describing only the apparent topic from the title. "
                "Begin with '제목 기준:' and do not claim any method, evidence, or finding. Infer only the primary "
                "topic and up to two constructs that are explicit in the title. Set method to '방법 미상'."
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
        article.constructs = [" ".join(item.split()) for item in parsed["constructs"] if item.strip()][:2]


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
