from __future__ import annotations

from collections import OrderedDict
from datetime import date
from html import escape, unescape
import os
import re

from .config import FIELDS, JOURNAL_FIELD, JOURNAL_RANK, JOURNAL_TIER, JOURNALS
from .models import Article


# One sans for Latin and Hangul alike. Pretendard is linked in <head> for clients that load
# web fonts (Apple Mail, iOS Mail); everywhere else the platform's own UI sans takes over:
# SF + Apple SD Gothic Neo on Apple, Segoe UI + Malgun Gothic on Windows, Roboto + Noto Sans
# KR on Android and Gmail. Helvetica and Arial stay as the last Latin fallbacks.
SANS = (
    "Pretendard,-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Segoe UI','Malgun Gothic',"
    "'Noto Sans KR',Roboto,'Helvetica Neue',Helvetica,Arial,sans-serif"
)
PRETENDARD_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"

# Cool index-card paper with slate ink. Each field (and the 기타 fallback) has its
# own colour, used for its outlined section box, journal names, the field counts in
# the header, and the topic tag of its articles.
PAGE = "#e9edf1"
SURFACE = "#ffffff"
INK = "#1d2733"
MUTED = "#5a6472"
# The English abstract: quieter than the Korean summary, still easy to read at length.
BODY = "#3d4754"
RULE = "#e3e8ee"
# Dots and other separators: present, never louder than the text they separate.
FAINT = "#a3acb8"
FIELD_COLORS: dict[str, str] = {
    "행정·정책": "#1f5f8b",
    "정치학": "#8c3a5b",
    "경영·조직": "#2e7350",
    "정보시스템": "#5847a0",
    "AI 심리": "#13707a",
}
# Pale fills for the field heading boxes only; paper boxes stay white.
FIELD_TINTS: dict[str, str] = {
    "행정·정책": "#e6eff6",
    "정치학": "#f5e8ee",
    "경영·조직": "#e5f1ea",
    "정보시스템": "#ece9f6",
    "AI 심리": "#e2f1f2",
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


def _tint_for_color(color: str) -> str:
    for field, field_color in FIELD_COLORS.items():
        if field_color == color:
            return FIELD_TINTS[field]
    return FALLBACK_TINT


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
            else f'<i style="color:{FAINT}">소속 정보 없음</i>'
        )
        rows.append(
            f'<div style="margin:1px 0"><b style="color:{INK};font-weight:600">{escape(author)}</b>'
            f'<b style="font-weight:normal;color:{FAINT}">&nbsp;·&nbsp;</b>{place}</div>'
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
    # Plain inline text joined by dots: no chip borders, so the tags read as one quiet line
    # instead of a row of buttons. Each tag stays whole; the line wraps between tags.
    dot = f'<b style="font-weight:normal;color:{FAINT}">&nbsp;&nbsp;·</b> '
    chips = dot.join(
        f'<b style="font-weight:600;color:{tag_color};white-space:nowrap">{escape(value)}</b>'
        for value, tag_color in tags
    )
    return f'<div style="margin-top:10px;font-family:{SANS};font-size:12px;line-height:1.8">{chips}</div>'


def _article_html(article: Article, color: str, first: bool) -> str:
    link = escape(article.url, quote=True)
    doi_url = "https://doi.org/" + article.doi if article.doi else article.url
    doi_label = doi_url.removeprefix("https://")
    if article.abstract:
        body = re.sub(r"^\s*abstract[\s:.\-–—]*", "", article.abstract, flags=re.IGNORECASE)
        abstract = (
            f'<div style="margin-top:16px;font-family:{SANS};font-size:14px;line-height:1.7;color:{BODY}">'
            f'<b style="color:{INK};font-weight:600">Abstract</b>&nbsp;&nbsp;{escape(body or article.abstract)}</div>'
        )
    else:
        abstract = (
            f'<div style="margin-top:14px;font-family:{SANS};font-size:13px;line-height:1.6;'
            f'color:{MUTED}">공개된 초록이 없어 제목만 보고 요약했습니다. (Abstract unavailable)</div>'
        )
    summary = escape(article.summary_ko or "요약을 만들지 못했습니다.")
    if article.ai_related:
        summary = (
            # Horizontal padding only: vertical padding on an inline element spills outside
            # the line box and makes the badge look taller than the text around it.
            f'<b style="padding:0 6px;background:{AI_BADGE};border-radius:3px;font-size:13px;'
            f'font-weight:bold;color:#ffffff;white-space:nowrap">{AI_LABEL}</b> {summary}'
        )
    rule = "" if first else f"border-top:1px solid {RULE};"
    return (
        f'<tr><td class="paper" style="{rule}padding:26px 0 28px;font-family:{SANS};text-align:left">'
        f'<h3 class="en-title" style="margin:0;font-family:{SANS};font-size:19px;line-height:1.35;'
        f'font-weight:bold;color:{INK}">'
        f'<a href="{link}" style="color:{INK};text-decoration:none">{escape(article.title)}</a></h3>'
        f'<div style="margin-top:8px;font-family:{SANS};font-size:12px;line-height:1.55;color:{MUTED}">'
        f'{_affiliations_html(article)}</div>'
        f'{_tags_html(article, color)}'
        # The Korean summary is the reason to open the email, so it gets the one tinted panel.
        '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" '
        f'style="margin-top:14px;background:{_tint_for_color(color)};border-radius:6px"><tr>'
        f'<td class="ko-sum" style="padding:14px 18px;font-family:{SANS};font-size:15px;line-height:1.75;word-break:keep-all;'
        f'color:{INK}">{summary}</td></tr></table>'
        f'{abstract}'
        f'<div style="margin-top:14px;font-family:{SANS};font-size:13px;line-height:1.6;color:{MUTED}">'
        f'<a href="{link}" style="font-weight:bold;color:{color};text-decoration:none">논문 보기 →</a>'
        f'<b style="font-weight:normal;color:{FAINT}">&nbsp;&nbsp;·</b> '
        f'온라인 게재 {escape(article.publication_date.isoformat())}'
        f'<b style="font-weight:normal;color:{FAINT}">&nbsp;&nbsp;·</b> '
        f'<a href="{escape(doi_url, quote=True)}" style="color:{MUTED};text-decoration:underline;'
        f'word-break:break-all">{escape(doi_label)}</a></div>'
        '</td></tr>'
    )


def _field_index_html(field_counts: OrderedDict[str, int], ai_count: int = 0) -> str:
    """The field counts as one wrapping line, each underlined in its field colour."""
    items = [
        f'<b style="padding-bottom:3px;border-bottom:3px solid {_colors(field)};font-weight:normal;'
        f'color:{_colors(field)};white-space:nowrap">{escape(field)} <b>{count}</b>편</b>'
        for field, count in field_counts.items()
    ]
    if ai_count:
        items.append(
            f'<b style="padding-bottom:3px;border-bottom:3px solid {AI_BADGE};color:{AI_BADGE};'
            f'white-space:nowrap">{AI_LABEL} {ai_count}편</b>'
        )
    # Inline items wrap like words, so a phone gets two or three lines with nothing pushed off screen.
    return (
        f'<div style="margin-top:20px;font-family:{SANS};font-size:14px;line-height:2.6">'
        + "&nbsp;&nbsp;&nbsp;&nbsp; ".join(items)
        + "</div>"
    )


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
            '<tr><td style="padding:44px 0 0">'
            '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" '
            f'style="background:{color};border-radius:6px"><tr>'
            f'<td class="ko-field" style="padding:12px 18px;font-family:{SANS};font-size:17px;line-height:1.3;'
            f'font-weight:bold;color:#ffffff">{escape(field)}</td>'
            f'<td align="right" style="padding:12px 18px;font-family:{SANS};font-size:14px;'
            f'line-height:1.3;color:#ffffff;white-space:nowrap">{field_counts[field]}편</td>'
            '</tr></table></td></tr>'
        ]
        text_entries: list[str] = []
        for journal, journal_articles in journals.items():
            blocks.append(
                f'<tr><td style="padding:28px 0 0;font-family:{SANS};text-align:left">'
                f'<div style="padding-bottom:10px;border-bottom:2px solid {color};font-size:15px;line-height:1.4">'
                f'<b style="color:{color}">{escape(journal)}</b>'
                f'<b style="font-weight:normal;color:{MUTED}">&nbsp;&nbsp;Tier {JOURNAL_TIER.get(journal, 3)}, '
                f'{len(journal_articles)}편</b></div></td></tr>'
            )
            blocks.extend(
                _article_html(article, color, index == 0) for index, article in enumerate(journal_articles)
            )
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
        strip = _field_index_html(field_counts, sum(article.ai_related for article in articles))
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
    # With papers, the field counts under the masthead say it all; the sentence is for the empty day.
    heading = (
        ""
        if sections
        else (
            f'<div class="ko-head" style="margin-top:18px;font-family:{SANS};font-size:18px;line-height:1.5;'
            f'font-weight:600;color:{INK}">{headline}</div>'
        )
    )
    html_body = f"""<!doctype html>
<html lang="ko"><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<link href="{PRETENDARD_CSS}" rel="stylesheet">
<style>
  html, body, table, td, a {{ -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  table, td {{ mso-table-lspace:0pt; mso-table-rspace:0pt; }}
  table {{ border-collapse:collapse !important; }}
  a:hover {{ text-decoration:underline !important; }}
  a:focus-visible {{ outline:2px solid {INK}; outline-offset:2px; }}
  @media only screen and (max-width:940px) {{ .shell {{ width:100% !important; }} .outer {{ padding:0 !important; }} .pad {{ padding-left:20px !important; padding-right:20px !important; }} }}
  /* Hangul fills its em box, so it reads larger than Latin text at the same size; on phones step it down further. */
  @media only screen and (max-width:600px) {{ .ko-sum {{ font-size:14px !important; line-height:1.7 !important; padding:12px 14px !important; }} .ko-head, .ko-field {{ font-size:15px !important; }} .en-title {{ font-size:17px !important; }} .paper {{ padding:22px 0 24px !important; }} .masthead {{ font-size:22px !important; }} }}
</style>
<!--[if mso]><style>body,table,td,a,h1,h3,div {{font-family:'Malgun Gothic',Arial,sans-serif !important;}}</style><![endif]-->
</head><body style="width:100%;margin:0;padding:0;background:{PAGE};font-family:{SANS};color:{INK};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden">{escape(preheader)}</div>
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="width:100%;background:{PAGE}"><tr><td align="center" class="outer" style="padding:28px 12px">
<!--[if mso]><table role="presentation" width="900" border="0" cellspacing="0" cellpadding="0"><tr><td width="900"><![endif]-->
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" class="shell" style="width:100%;max-width:900px;background:{SURFACE};border-radius:8px">
  <tr><td style="height:6px;line-height:6px;font-size:0;background:{INK};border-radius:8px 8px 0 0">&nbsp;</td></tr>
  <tr><td class="pad" style="padding:30px 44px 32px;font-family:{SANS};text-align:left;border-bottom:1px solid {RULE}">
    <div style="font-family:{SANS};font-size:14px;line-height:1.4;color:{MUTED}">{_date_ko(digest_date)}</div>
    <h1 class="masthead" style="margin:6px 0 0;font-family:{SANS};font-size:26px;line-height:1.2;font-weight:800;letter-spacing:-0.3px;color:{INK}">PA Journal Daily Digest</h1>
    {heading}
    {strip}
  </td></tr>
  <tr><td class="pad" style="padding:0 44px;text-align:left">
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">{content_html}</table>
  </td></tr>
  <tr><td class="pad" style="padding:40px 44px 40px;font-family:{SANS};font-size:13px;line-height:1.6;color:{MUTED};text-align:left">
    <div style="padding-top:28px;border-top:1px solid {RULE}">
      <table role="presentation" border="0" cellspacing="0" cellpadding="0"><tr>
        <td style="background:{INK};border-radius:6px">
          <a href="{escape(archive_url, quote=True)}" style="display:block;padding:12px 20px;font-family:{SANS};font-size:14px;font-weight:bold;line-height:1.2;color:#ffffff;text-decoration:none">누적 논문 정리표 다운로드 (XLSX)</a>
        </td>
      </tr></table>
      <div style="margin-top:16px">Crossref와 공개 학술 메타데이터로 자동 생성한 메일입니다. 한국어 요약은 초록을 바탕으로 쓰며 원문을 대체하지 않습니다.</div>
    </div>
  </td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table></body></html>"""
    text_body = (
        f"PA Journal Daily Digest\n{_date_ko(digest_date)}\n{headline}\n\n"
        + content_text
        + "\n\n자동 생성 요약은 원문 초록을 대체하지 않습니다."
        + "\n누적 논문 정리표 (XLSX): "
        + archive_url
    )
    return subject, html_body, text_body
