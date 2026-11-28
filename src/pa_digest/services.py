from __future__ import annotations

import json
import os

import httpx
from openai import OpenAI

from .config import JOURNALS
from .models import Article

AI_OR_PA_SHORT_NAMES = {journal.short_name for journal in JOURNALS if journal.ai_or_pa_only}


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
        "pa_related": {"type": "boolean"},
        "is_editorial": {"type": "boolean"},
    },
    "required": [
        "summary_ko",
        "topic_area",
        "method",
        "method_detail",
        "constructs",
        "ai_related",
        "pa_related",
        "is_editorial",
    ],
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
                + PA_RELATED_RULE
                + EDITORIAL_RULE
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
                + PA_RELATED_RULE
                + EDITORIAL_RULE
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
        # Independent of the batch screen: for screened journals the CLI drops papers that this
        # second, per-paper read does not confirm (AI-related, or for AI-or-PA journals either flag).
        article.ai_related = bool(parsed.get("ai_related", False))
        article.pa_related = bool(parsed.get("pa_related", False))
        article.is_editorial = bool(parsed.get("is_editorial", False))


    def select_ai_social(self, articles: list[Article]) -> list[Article]:
        """Keep only the screened journals' articles that fit the reader's interests.

        AI-only journals (psychology, NHB, PNAS, Science, Nature) keep articles whose subject is AI as
        it bears on politics or psychology. AI-or-PA journals (PolBeh, PolComm, POQ, JEPS, PolPsych) also keep
        articles about public administration. Candidates are judged in batches on title and abstract,
        so one call covers a whole week of PNAS.
        """
        ai_or_pa = bool(articles) and articles[0].journal_short in AI_OR_PA_SHORT_NAMES
        instructions = AI_OR_PA_FILTER_INSTRUCTIONS if ai_or_pa else AI_FILTER_INSTRUCTIONS
        kept: list[Article] = []
        for start in range(0, len(articles), AI_FILTER_BATCH):
            chunk = articles[start : start + AI_FILTER_BATCH]
            listing = "\n\n".join(
                f"[{index}] {article.title}\n{article.abstract or '(no abstract)'}"
                for index, article in enumerate(chunk)
            )
            response = self.client.responses.create(
                model=self.model,
                reasoning={"effort": "low"},
                input=[
                    {"role": "system", "content": instructions},
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
                    if not ai_or_pa:
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
    "Set ai_related to true only when BOTH hold. (1) AI itself is what the article studies: large "
    "language models, chatbots, generative AI, AI agents, algorithms or algorithmic decision-making, "
    "recommender systems, or automation by AI. (2) The article studies people or society in relation to "
    "that AI: how individuals, voters, workers, citizens, organizations or governments use, judge, trust, "
    "are persuaded or affected by, adopt, regulate or govern it. Ask: are humans or social institutions "
    "measured or analysed in relation to the AI? If the article only tests, benchmarks, builds or "
    "applies an AI model, the answer is no. "
    "Set it to false when AI is a scientific or analytic tool: protein, chromatin or genome models such "
    "as AlphaFold, medical diagnosis or imaging models, drug or materials discovery, weather and climate "
    "models, physics or chemistry simulations, and machine learning used to measure or estimate "
    "something that is not about AI (for example a credit-market or health study that uses a "
    "machine-learning model to estimate effects, or an LLM used to code survey answers). "
    "Set it to false for social-science papers whose subject is something else, such as sleep loss and "
    "phishing, cybersecurity, social media, the internet, digital government or bureaucratic incentives, "
    "unless AI itself is what is being studied."
)
PA_RELATED_RULE = (
    " Set pa_related to true only when public administration or public management is a central "
    "subject: bureaucracy and bureaucrats, civil servants and public employees, government agencies "
    "and their performance, public service delivery, street-level or front-line work, policy "
    "implementation by administrators, red tape and administrative burden, regulation as carried out by "
    "agencies, representative bureaucracy, or how citizens perceive, trust or interact with public "
    "agencies and services. Set it to false when the article is about elections, voting, parties, "
    "candidates, legislatures, campaigns, partisanship, media coverage or public opinion in general and "
    "public administration is only background."
)
EDITORIAL_RULE = (
    " Set is_editorial to true when the item is written by or for the journal's editors rather than "
    "reporting research: an editorial, an editor's note or letter, an editor's or guest editors' "
    "introduction to a special issue, symposium or section that mainly previews the papers in it, an "
    "announcement or a tribute. Set it to false for original research, systematic or narrative "
    "reviews, and theoretical articles, even when they appear in a special issue."
)
AI_FILTER_BATCH = 40
AI_FILTER_SCHEMA = {
    "type": "object",
    "properties": {"relevant": {"type": "array", "items": {"type": "integer"}}},
    "required": ["relevant"],
    "additionalProperties": False,
}
AI_FILTER_INSTRUCTIONS = (
    "You screen new articles from broad science and psychology journals for a political scientist and "
    "public administration scholar who studies AI from a social-science perspective. Return the indices "
    "of articles that meet BOTH conditions:\n"
    "1. AI itself is what the article studies: large language models, chatbots, generative AI, AI agents, "
    "algorithms or algorithmic decision-making, recommender systems, or automation by AI. The title or "
    "abstract must name such a system.\n"
    "2. The article studies people or society in relation to that AI: politics, government, public "
    "opinion, persuasion, beliefs, misinformation, trust, moral or social judgment, work and "
    "organizations, or human psychology and behaviour toward or with AI. Humans or social institutions "
    "must be measured or analysed, not only the model.\n"
    "A social-science paper that does not study AI fails condition 1. An article that only tests, "
    "benchmarks, builds or applies an AI model fails condition 2, whatever the field. AI used as a "
    "scientific or analytic tool always fails: protein, chromatin or genome models such as AlphaFold, "
    "medical diagnosis or imaging models, drug or materials discovery, weather and climate models, "
    "physics or chemistry simulations, and machine learning used to measure or predict something that is "
    "not about AI.\n\n"
    "Typical articles to keep:\n"
    "- Costello, Pennycook and Rand: conversations with an LLM durably reduce belief in conspiracy "
    "theories.\n"
    "- Myra Cheng and colleagues: sycophantic LLMs affirm users, and this shapes users' judgments, "
    "prosocial intentions and reliance on AI.\n"
    "- AI-written political messages persuading voters; LLMs simulating survey respondents; public "
    "attitudes toward AI in government; AI and political polarization or misinformation.\n"
    "- People judging or evaluating AI output, for example 100 research group leaders rating "
    "scientific ideas generated by LLMs and knowledge graphs.\n\n"
    "Typical articles to exclude:\n"
    "- A chromatin biology assessment of AlphaFold3 (the model is benchmarked; no people are studied).\n"
    "- A deep-learning model that reads chest X-rays or predicts disease (medical AI).\n"
    "- Modest sleep loss after the daylight-saving shift raises clicks on simulated phishing emails "
    "(no AI is studied).\n"
    "- Bureaucratic incentives under China's one vote veto shaped the one-child policy (no AI).\n"
    "- An LLM used only to code open-ended survey answers in a study of something else.\n\n"
    "Keep only original research articles and research reviews. Exclude commentary of any kind: "
    "news stories, editorials, comments, perspectives, opinion and policy-forum pieces, News & Views, "
    "replies and letters, Q&As, research highlights, obituaries and book reviews. "
    "When unsure, exclude. Return an empty list when nothing qualifies."
)
AI_OR_PA_FILTER_INSTRUCTIONS = (
    "You screen new articles from political behaviour, political communication and public opinion "
    "journals for a public administration scholar who also studies AI from a social-science "
    "perspective. Return the indices of articles that meet AT LEAST ONE condition:\n"
    "A. AI: AI itself (large language models, chatbots, generative AI, AI agents, algorithms or "
    "algorithmic decision-making, recommender systems, automation by AI) is what the article studies, "
    "and people or society are studied in relation to it, for example AI-written persuasion, "
    "AI-generated misinformation, public attitudes toward AI, or LLMs simulating survey respondents.\n"
    "B. Public administration: bureaucracy and bureaucrats, civil servants and public employees, "
    "government agencies and their performance, public service delivery, street-level or front-line "
    "work, policy implementation, red tape and administrative burden, representative bureaucracy, or how "
    "citizens perceive, trust or interact with public agencies and services.\n"
    "Exclude articles about elections, voting, turnout, parties, candidates, legislatures, campaigns, "
    "partisanship, polarization, media coverage or public opinion in general when neither AI nor public "
    "administration is a central subject. Exclude articles that use machine learning or an LLM only as a "
    "measurement tool, for example to code texts or survey answers.\n\n"
    "Typical articles to keep:\n"
    "- Citizens' trust in government agencies after a service failure (B).\n"
    "- A survey experiment on how administrative burden shapes take-up of public benefits (B).\n"
    "- Partisan bias in how voters judge bureaucrats' performance (B).\n"
    "- AI-written political messages persuading voters (A).\n\n"
    "Typical articles to exclude:\n"
    "- Negative campaign ads and turnout in US House races.\n"
    "- Affective polarization on social media.\n"
    "- A topic model of party manifestos used to measure ideology.\n\n"
    "Keep only original research articles and research reviews. When unsure, exclude. Return an empty "
    "list when nothing qualifies."
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
