from __future__ import annotations

from collections import OrderedDict
from datetime import date
from html import escape, unescape
import os

from .config import FIELDS, JOURNAL_FIELD, JOURNAL_RANK, JOURNAL_TIER, JOURNALS
from .models import Article


# Helvetica for everything; Helvetica has no Hangul, so Korean falls back to the
# platform's Korean sans. All of these are email-safe (web fonts are blocked in
# Gmail and Outlook).
SANS = "'Helvetica Neue',Helvetica,Arial,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"

# Cool index-card paper with slate ink. Each field (and the 기타 fallback) has its
# own colour, used for its outlined section box, journal names, the field counts in
# the header, and the topic tag of its articles.
PAGE = "#e9edf1"
SURFACE = "#ffffff"
INK = "#1d2733"
MUTED = "#5a6472"
RULE = "#d8dee5"
# Faint outline around each paper: visible enough to group a paper, quiet next to the field boxes.
PAPER_LINE = "#e6eaef"
FIELD_COLORS: dict[str, str] = {
    "행정·정책": "#1f5f8b",
    "정치학": "#8c3a5b",
    "경영·조직": "#2e7350",
    "심리학": "#8a600c",
    "정보시스템": "#5847a0",
    "AI·사회과학": "#13707a",
}
# Pale fills for the field heading boxes only; paper boxes stay white.
FIELD_TINTS: dict[str, str] = {
    "행정·정책": "#e6eff6",
    "정치학": "#f5e8ee",
    "경영·조직": "#e5f1ea",
    "심리학": "#f6eedc",
    "정보시스템": "#ece9f6",
    "AI·사회과학": "#e2f1f2",
}
FALLBACK_TINT = "#f3ebe3"
FALLBACK_FIELD = "기타"
FALLBACK_COLOR = "#7a4f2a"
# The one loud mark in the email: a filled badge on papers whose subject is AI.
AI_BADGE = "#d6246e"
AI_LABEL = "🤖 AI"
WEEKDAYS_KO = ("월", "화", "수", "목", "금", "토", "일")
DEFAULT_ARCHIVE_URL = (
    "https://github.com/SangwonJu/pa-journal-digest/raw/refs/heads/main/"
    "data/PA_Journal_Digest_Archive.xlsx"
)


def _field(journal: str) -> str:
    return JOURNAL_FIELD.get(journal, FALLBACK_FIELD)


def _tint(field: str) -> str:
    return FIELD_TINTS.get(field, FALLBACK_TINT)


def _colors(field: str) -> str:
    return FIELD_COLORS.get(field, FALLBACK_COLOR)


def _field_order(field: str) -> int:
    return FIELDS.index(field) if field in FIELDS else len(FIELDS)


def _date_ko(value: date) -> str:
    return f"{value.year}년 {value.month}월 {value.day}일 {WEEKDAYS_KO[value.weekday()]}요일"


def _method_label(article: Article) -> str:
    method = article.method or "방법 미상"
    if article.method_detail and method != "방법 미상":
        method = f"{method} ({article.method_detail})"
    return method


def _affiliations_html(article: Article) -> str:
    if not article.authors:
        return f'<div style="color:{MUTED}">저자 정보 없음</div>'
    rows: list[str] = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        place = (
            escape(unescape("; ".join(affiliations)))
            if affiliations
            else f'<i style="color:{MUTED}">소속 정보 없음</i>'
        )
        rows.append(
            f'<div style="margin:2px 0"><b style="color:{INK};font-weight:600">{escape(author)}</b>, {place}</div>'
        )
    return "".join(rows)


def _affiliations_text(article: Article) -> str:
    if not article.authors:
        return "저자 정보 없음"
    rows = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        place = unescape("; ".join(affiliations)) if affiliations else "소속 정보 없음"
        rows.append(f"{author}, {place}")
    return "\n".join(rows)


def _tags_html(article: Article, color: str) -> str:
    tags = [(article.topic_area or "분야 미상", color), (_method_label(article), INK)]
    tags.extend((construct, MUTED) for construct in article.constructs[:2])
    # Inline-block chips wrap onto a new line on phones instead of widening the email.
    chips = "".join(
        f'<div style="display:inline-block;margin:0 6px 6px 0;padding:3px 8px;border:1px solid {RULE};'
        f'border-radius:3px;font-size:12px;line-height:1.3;color:{tag_color};white-space:nowrap">'
        f'<strong style="font-weight:600">{escape(value)}</strong></div>'
        for value, tag_color in tags
    )
    return f'<div style="margin:12px 0 4px;font-family:{SANS}">{chips}</div>'


def _article_html(article: Article, color: str) -> str:
    link = escape(article.url, quote=True)
    doi_url = "https://doi.org/" + article.doi if article.doi else article.url
    if article.abstract:
        abstract = (
            f'<div style="margin-top:14px;font-family:{SANS};font-size:14px;line-height:1.7;'
            f'color:{MUTED}">{escape(article.abstract)}</div>'
        )
    else:
        abstract = (
            f'<div style="margin-top:12px;font-family:{SANS};font-size:13px;line-height:1.6;'
            f'color:{MUTED}">공개된 초록이 없어 제목만 보고 요약했습니다. (Abstract unavailable)</div>'
        )
    summary = escape(article.summary_ko or "요약을 만들지 못했습니다.")
    if article.ai_related:
        summary = (
            f'<b style="display:inline-block;margin:0 10px 4px 0;padding:4px 11px;background:{AI_BADGE};'
            f'border-radius:4px;font-size:14px;line-height:1.3;font-weight:bold;color:#ffffff;'
            f'letter-spacing:.3px;vertical-align:1px;white-space:nowrap">{AI_LABEL}</b>{summary}'
        )
    return (
        '<tr><td style="padding:0 0 14px">'
        '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" '
        f'style="border:1px solid {PAPER_LINE}"><tr>'
        f'<td class="paper" style="padding:22px 24px 20px;font-family:{SANS};text-align:left">'
        f'<h3 class="en-title" style="margin:0;font-family:{SANS};font-size:19px;line-height:1.35;font-weight:bold;color:{INK}">'
        f'<a href="{link}" style="color:{INK};text-decoration:none">{escape(article.title)}</a></h3>'
        f'<div style="margin-top:8px;font-family:{SANS};font-size:13px;line-height:1.55;color:{MUTED}">'
        f'{_affiliations_html(article)}'
        f'<div style="margin-top:4px">온라인 게재 {escape(article.publication_date.isoformat())}</div></div>'
        f'{_tags_html(article, color)}'
        f'<div class="ko-sum" style="margin-top:6px;font-family:{SANS};font-size:15px;line-height:1.75;color:{INK}">{summary}</div>'
        f'{abstract}'
        f'<div style="margin-top:12px;font-family:{SANS};font-size:13px;line-height:1.5">'
        f'<a href="{link}" style="color:{color};text-decoration:underline;word-break:break-all">'
        f'{escape(doi_url)}</a></div>'
        '</td></tr></table></td></tr>'
    )


def _field_strip_html(field_counts: OrderedDict[str, int], ai_count: int = 0) -> str:
    items = "".join(
        f'<div style="display:inline-block;margin:0 18px 8px 0;font-family:{SANS};font-size:14px;'
        f'line-height:1.3;color:{_colors(field)};white-space:nowrap">{escape(field)} <b>{count}</b>편</div>'
        for field, count in field_counts.items()
    )
    if ai_count:
        items += (
            f'<div style="display:inline-block;margin:0 18px 8px 0;padding:1px 8px;background:{AI_BADGE};'
            f'border-radius:3px;font-family:{SANS};font-size:13px;line-height:1.4;font-weight:bold;'
            f'color:#ffffff;white-space:nowrap">{AI_LABEL} {ai_count}편</div>'
        )
    return f'<div style="margin-top:18px">{items}</div>'


def render_newsletter(articles: list[Article], digest_date: date) -> tuple[str, str, str]:
    count = len(articles)
    subject = f"[PA Journal Digest] {digest_date.isoformat()} 신규 {count}편"

    ordered = sorted(
        articles,
        key=lambda item: (
            _field_order(_field(item.journal)),
            JOURNAL_RANK.get(item.journal, 999),
            item.title.casefold(),
        ),
    )
    grouped: OrderedDict[str, OrderedDict[str, list[Article]]] = OrderedDict()
    for article in ordered:
        grouped.setdefault(_field(article.journal), OrderedDict()).setdefault(article.journal, []).append(article)
    field_counts = OrderedDict(
        (field, sum(len(items) for items in journals.values())) for field, journals in grouped.items()
    )
    journal_count = sum(len(journals) for journals in grouped.values())

    sections: list[str] = []
    text_sections: list[str] = []
    for field, journals in grouped.items():
        color = _colors(field)
        blocks = [
            '<tr><td style="padding:34px 0 0">'
            '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" '
            f'style="border:1px solid {color};background:{_tint(field)}"><tr>'
            f'<td class="ko-field" style="padding:10px 14px;font-family:{SANS};font-size:16px;line-height:1.3;'
            f'font-weight:bold;color:{color}">{escape(field)}</td>'
            f'<td align="right" style="padding:10px 14px;font-family:{SANS};font-size:14px;'
            f'line-height:1.3;color:{color};white-space:nowrap">{field_counts[field]}편</td>'
            '</tr></table></td></tr>'
        ]
        text_entries: list[str] = []
        for journal, journal_articles in journals.items():
            blocks.append(
                f'<tr><td style="padding:22px 0 10px;font-family:{SANS};text-align:left">'
                f'<div style="font-size:15px;line-height:1.4;font-weight:bold;color:{color}">{escape(journal)}</div>'
                f'<div style="margin-top:2px;font-size:13px;line-height:1.4;color:{MUTED}">'
                f'Tier {JOURNAL_TIER.get(journal, 3)}, {len(journal_articles)}편</div></td></tr>'
            )
            blocks.extend(_article_html(article, color) for article in journal_articles)
            for article in journal_articles:
                doi_url = "https://doi.org/" + article.doi if article.doi else article.url
                abstract_text = article.abstract or "Abstract unavailable (요약은 제목 기준)."
                tags = [article.topic_area or "분야 미상", _method_label(article), *article.constructs]
                text_entries.append(
                    f"{article.title}\n{journal} (Tier {JOURNAL_TIER.get(journal, 3)}), "
                    f"온라인 게재 {article.publication_date.isoformat()}\n"
                    f"{' '.join(f'[{tag}]' for tag in tags)}\n"
                    f"{_affiliations_text(article)}\n\n"
                    f"{f'[{AI_LABEL}] ' if article.ai_related else ''}"
                    f"한국어 요약: {article.summary_ko}\n\nEnglish abstract: {abstract_text}\n{doi_url}"
                )
        sections.append("".join(blocks))
        separator = "\n\n" + "-" * 40 + "\n\n"
        text_sections.append(f"■ {field} ({field_counts[field]}편)\n\n" + separator.join(text_entries))

    if sections:
        headline = f"새 논문 {count}편이 {journal_count}개 저널에서 들어왔습니다."
        content_html = "".join(sections)
        content_text = "\n\n\n".join(text_sections)
        strip = _field_strip_html(field_counts, sum(article.ai_related for article in articles))
        preheader = ", ".join(f"{field} {n}편" for field, n in field_counts.items())
    else:
        headline = "오늘은 새로 확인된 논문이 없습니다."
        follow_up = f"{len(JOURNALS)}개 저널을 모두 확인했습니다. 내일 새벽에 다시 확인합니다."
        content_html = (
            f'<tr><td style="padding:8px 0 44px;font-family:{SANS};font-size:15px;line-height:1.6;'
            f'color:{MUTED}">{follow_up}</td></tr>'
        )
        content_text = f"{headline} {follow_up}"
        strip = ""
        preheader = follow_up

    archive_url = os.getenv("DIGEST_ARCHIVE_URL", DEFAULT_ARCHIVE_URL)
    html_body = f"""<!doctype html>
<html lang="ko"><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<style>
  html, body, table, td, a {{ -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  table, td {{ mso-table-lspace:0pt; mso-table-rspace:0pt; }}
  table {{ border-collapse:collapse !important; }}
  a:focus-visible {{ outline:2px solid {INK}; outline-offset:2px; }}
  @media only screen and (max-width:940px) {{ .shell {{ width:100% !important; }} .outer {{ padding:0 !important; }} .pad {{ padding-left:18px !important; padding-right:18px !important; }} }}
  /* Hangul fills its em box, so it reads larger than Latin text at the same size; on phones step it down further. */
  @media only screen and (max-width:600px) {{ .ko-sum {{ font-size:14px !important; line-height:1.7 !important; }} .ko-head, .ko-field {{ font-size:15px !important; }} .en-title {{ font-size:17px !important; }} .paper {{ padding:16px 14px !important; }} }}
</style>
<!--[if mso]><style>body,table,td,a,h1,h3,div {{font-family:'Malgun Gothic',Arial,sans-serif !important;}}</style><![endif]-->
</head><body style="width:100%;margin:0;padding:0;background:{PAGE};font-family:{SANS};color:{INK};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden">{escape(preheader)}</div>
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="width:100%;background:{PAGE}"><tr><td align="center" class="outer" style="padding:28px 12px">
<!--[if mso]><table role="presentation" width="900" border="0" cellspacing="0" cellpadding="0"><tr><td width="900"><![endif]-->
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" class="shell" style="width:100%;max-width:900px;background:{SURFACE}">
  <tr><td class="pad" style="padding:32px 40px 26px;font-family:{SANS};text-align:left">
    <div style="font-size:14px;line-height:1.4;color:{MUTED}">{_date_ko(digest_date)}</div>
    <h1 style="margin:6px 0 0;font-family:{SANS};font-size:24px;line-height:1.3;font-weight:bold;color:{INK}">PA Journal Digest</h1>
    <div class="ko-head" style="margin-top:14px;font-size:16px;line-height:1.5;color:{INK}">{headline}</div>
    {strip}
  </td></tr>
  <tr><td class="pad" style="padding:0 40px;text-align:left">
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">{content_html}</table>
  </td></tr>
  <tr><td class="pad" style="padding:30px 40px 34px;font-family:{SANS};font-size:13px;line-height:1.6;color:{MUTED};text-align:left">
    <div style="padding-top:22px;border-top:2px solid {INK}">
      <a href="{escape(archive_url, quote=True)}" style="font-size:15px;font-weight:bold;color:{INK};text-decoration:underline">누적 논문 정리표 다운로드 (XLSX)</a>
      <div style="margin-top:10px">Crossref와 공개 학술 메타데이터로 자동 생성한 메일입니다. 한국어 요약은 초록을 바탕으로 쓰며 원문을 대체하지 않습니다.</div>
    </div>
  </td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table></body></html>"""
    text_body = (
        f"PA Journal Digest\n{_date_ko(digest_date)}\n{headline}\n\n"
        + content_text
        + "\n\n자동 생성 요약은 원문 초록을 대체하지 않습니다."
        + "\n누적 논문 정리표 (XLSX): "
        + archive_url
    )
    return subject, html_body, text_body
