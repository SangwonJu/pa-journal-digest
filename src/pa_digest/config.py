from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Journal:
    short_name: str
    name: str
    issns: tuple[str, ...]
    tier: int
    # When set, an LLM keeps only articles about AI in a political or psychological
    # context. Used for broad journals (NHB, PNAS, Science, Nature) and for the
    # psychology journals, where the reader follows AI-related work only.
    ai_social_only: bool = False
    # When set, an LLM keeps only articles that are about AI or about public administration.
    # Used for political behaviour, communication and opinion journals.
    ai_or_pa_only: bool = False

    @property
    def primary_issn(self) -> str:
        return self.issns[0]


# Tiers follow SCImago Journal Rank (SJR) 2025, retrieved 2026-11-28 from scimagojr.com
# (Scopus data as of March 2026). Each comment gives the SJR and the rank in the
# journal's main SCImago category. Within each field (see FIELDS below):
#   Tier 1: the top few journals of the field, cut where SJR drops sharply
#           (public administration is ranked within SCImago's Public Administration category);
#   Tier 2: other Q1 journals with SJR >= 1.5;
#   Tier 3: SJR below 1.5, or not indexed in Scopus.
# Journals are listed by field, then tier, then SJR; the newsletter keeps this order.
JOURNALS: tuple[Journal, ...] = (
    # SJR 3.305; Public Administration #2/246
    Journal("PAR", "Public Administration Review", ("0033-3352", "1540-6210"), 1),
    # SJR 3.301; Public Administration #3/246
    Journal("JPART", "Journal of Public Administration Research and Theory", ("1053-1858", "1477-9803"), 1),
    # SJR 2.723; Public Administration #4/246
    Journal("PA", "Public Administration", ("0033-3298", "1467-9299"), 2),
    # SJR 2.540; Public Administration #5/246
    Journal("PMR", "Public Management Review", ("1471-9037", "1471-9045"), 2),
    # SJR 3.575; not in the Public Administration category (Sociology & Political Science #13/1513)
    Journal("GIQ", "Government Information Quarterly", ("0740-624X", "1872-9517"), 2),
    # SJR 1.988; Public Administration #8/246
    Journal("PPMG", "Perspectives on Public Management and Governance", ("2398-4910", "2398-4929"), 2),
    # SJR 1.952; Public Administration #9/246
    Journal("ROPPA", "Review of Public Personnel Administration", ("0734-371X", "1552-759X"), 2),
    # SJR 1.741; Public Administration #12/246
    Journal("JPAM", "Journal of Policy Analysis and Management", ("0276-8739", "1520-6688"), 2),
    # SJR 1.581; Public Administration #13/246
    Journal("Governance", "Governance", ("0952-1895", "1468-0491"), 2),
    # SJR 1.363; Public Administration #20/246
    Journal("PSJ", "Policy Studies Journal", ("0190-292X", "1541-0072"), 3),
    # SJR 1.226; Public Administration #27/246
    Journal("IPMJ", "International Public Management Journal", ("1096-7494", "1559-3169"), 3),
    # SJR 1.221; Public Administration #28/246
    Journal("ARPA", "The American Review of Public Administration", ("0275-0740", "1552-3357"), 3),
    # SJR 1.097; Public Administration #34/246
    Journal("PPMR", "Public Performance & Management Review", ("1530-9576", "1557-9271"), 3),
    # SJR 1.073; Public Administration #37/246
    Journal("A&S", "Administration & Society", ("0095-3997", "1552-3039"), 3),
    # not indexed in Scopus/SCImago
    Journal("JBPA", "Journal of Behavioral Public Administration", ("2576-6465",), 3),
    # SJR 6.539; Political Science & IR #1/725
    Journal("AJPS", "American Journal of Political Science", ("0092-5853", "1540-5907"), 1),
    # SJR 5.433; Political Science & IR #2/725
    Journal("APSR", "American Political Science Review", ("0003-0554", "1537-5943"), 1),
    # SJR 4.368; Political Science & IR #3/725
    Journal("PolAnalysis", "Political Analysis", ("1047-1987", "1476-4989"), 1),
    # SJR 3.492; Sociology & Political Science #15/1513
    Journal("JOP", "The Journal of Politics", ("0022-3816", "1468-2508"), 2),
    # SJR 2.955; Sociology & Political Science #26/1513
    Journal("PolBeh", "Political Behavior", ("0190-9320", "1573-6687"), 2, ai_or_pa_only=True),
    # SJR 2.907; Sociology & Political Science #27/1513
    Journal("PolComm", "Political Communication", ("1058-4609", "1091-7675"), 2, ai_or_pa_only=True),
    # SJR 2.191; Sociology & Political Science #43/1513
    Journal("POQ", "Public Opinion Quarterly", ("0033-362X", "1537-5331"), 2, ai_or_pa_only=True),
    # SJR 2.016; Sociology & Political Science #50/1513
    Journal("JEPS", "Journal of Experimental Political Science", ("2052-2630", "2052-2649"), 2, ai_or_pa_only=True),
    # SJR 1.938; Political Science & IR #19/725 (Social Psychology #14/318)
    Journal("PolPsych", "Political Psychology", ("0162-895X", "1467-9221"), 2, ai_or_pa_only=True),
    # SJR 14.367; Organizational Behavior & HRM #2/262
    Journal("AMA", "Academy of Management Annals", ("1941-6520", "1941-6067"), 1),
    # SJR 10.781; Strategy & Management #3/518
    Journal("AMJ", "Academy of Management Journal", ("0001-4273", "1948-0989"), 1),
    # SJR 10.154; Strategy & Management #4/518
    Journal("SMJ", "Strategic Management Journal", ("0143-2095", "1097-0266"), 1),
    # SJR 9.996; Strategy & Management #5/518
    Journal("AMR", "Academy of Management Review", ("0363-7425", "1930-3807"), 1),
    # SJR 8.251; Strategy & Management #6/518
    Journal("JOM", "Journal of Management", ("0149-2063", "1557-1211"), 2),
    # SJR 7.929; Organizational Behavior & HRM #3/262
    Journal("OrgSci", "Organization Science", ("1047-7039", "1526-5455"), 2),
    # SJR 5.473; Applied Psychology #3/270
    Journal("JAP", "Journal of Applied Psychology", ("0021-9010", "1939-1854"), 2),
    # SJR 3.999; Organizational Behavior & HRM #12/262
    Journal("JOB", "Journal of Organizational Behavior", ("0894-3796", "1099-1379"), 2),
    # SJR 3.152; Organizational Behavior & HRM #15/262
    Journal("OBHDP", "Organizational Behavior and Human Decision Processes", ("0749-5978", "1095-9920"), 2),
    # SJR 8.496; Psychology (misc.) #2/347
    Journal("PsychBull", "Psychological Bulletin", ("0033-2909", "1939-1455"), 1, ai_social_only=True),
    # SJR 6.292; Social Psychology #2/318
    Journal("PSPR", "Personality and Social Psychology Review", ("1088-8683", "1532-7957"), 1, ai_social_only=True),
    # SJR 3.767; Social Psychology #4/318
    Journal("JPSP", "Journal of Personality and Social Psychology", ("0022-3514", "1939-1315"), 2, ai_social_only=True),
    # SJR 3.072; Human-Computer Interaction #5/204, Psychology (misc.) #11/347
    Journal("CHB", "Computers in Human Behavior", ("0747-5632",), 2, ai_social_only=True),
    # SJR 2.309; Psychology (misc.) #17/347
    Journal("PsychSci", "Psychological Science", ("0956-7976", "1467-9280"), 2, ai_social_only=True),
    # SJR 2.179; Social Psychology #11/318
    Journal("SPPS", "Social Psychological and Personality Science", ("1948-5506", "1948-5514"), 2, ai_social_only=True),
    # SJR 2.086; Social Psychology #13/318
    Journal("PSPB", "Personality and Social Psychology Bulletin", ("0146-1672", "1552-7433"), 2, ai_social_only=True),
    # SJR 1.896; Social Psychology #15/318
    Journal("JESP", "Journal of Experimental Social Psychology", ("0022-1031", "1096-0465"), 2, ai_social_only=True),
    # SJR 5.679; Management Information Systems #2/144
    Journal("ISR", "Information Systems Research", ("1047-7047", "1526-5536"), 1),
    # SJR 4.061; Management Information Systems #3/144
    Journal("MISQ", "MIS Quarterly", ("0276-7783", "2162-9730"), 1),
    # SJR 19.713; Multidisciplinary #1/233
    Journal("Nature", "Nature", ("0028-0836", "1476-4687"), 1, ai_social_only=True),
    # SJR 10.948; Multidisciplinary #2/233
    Journal("Science", "Science", ("0036-8075", "1095-9203"), 1, ai_social_only=True),
    # SJR 4.896; Social Psychology #3/318
    Journal("NHB", "Nature Human Behaviour", ("2397-3374",), 2, ai_social_only=True),
    # SJR 3.283; Multidisciplinary #7/233
    Journal("PNAS", "Proceedings of the National Academy of Sciences", ("0027-8424", "1091-6490"), 2, ai_social_only=True),
)

JOURNAL_BY_NAME = {journal.name: journal for journal in JOURNALS}
JOURNAL_RANK = {journal.name: rank for rank, journal in enumerate(JOURNALS, start=1)}
JOURNAL_TIER = {journal.name: journal.tier for journal in JOURNALS}

# Fields group the newsletter into the reader's disciplines. The order here is
# the order of sections in the email; within a field, journals keep JOURNALS order.
FIELDS: tuple[str, ...] = ("행정·정책", "정치학", "경영·조직", "심리학", "정보시스템", "AI·사회과학")
_FIELD_BY_SHORT = {
    **dict.fromkeys(
        ("JPART", "PAR", "PPMG", "JPAM", "PMR", "PA", "ARPA", "PSJ", "IPMJ",
         "PPMR", "GIQ", "Governance", "A&S", "ROPPA", "JBPA"),
        "행정·정책",
    ),
    **dict.fromkeys(
        ("AJPS", "APSR", "JOP", "PolAnalysis", "PolBeh", "POQ", "PolComm", "JEPS", "PolPsych"), "정치학"
    ),
    **dict.fromkeys(("AMJ", "AMR", "AMA", "JOB", "JOM", "SMJ", "OrgSci", "OBHDP", "JAP"), "경영·조직"),
    **dict.fromkeys(
        ("JPSP", "PSPB", "PsychSci", "PsychBull", "PSPR", "JESP", "SPPS", "CHB"), "심리학"
    ),
    **dict.fromkeys(("MISQ", "ISR"), "정보시스템"),
    **dict.fromkeys(("NHB", "PNAS", "Science", "Nature"), "AI·사회과학"),
}
JOURNAL_FIELD = {journal.name: _FIELD_BY_SHORT[journal.short_name] for journal in JOURNALS}

