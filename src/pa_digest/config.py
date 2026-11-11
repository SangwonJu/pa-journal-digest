from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Journal:
    short_name: str
    name: str
    issns: tuple[str, ...]
    tier: int

    @property
    def primary_issn(self) -> str:
        return self.issns[0]


JOURNALS: tuple[Journal, ...] = (
    Journal("JPART", "Journal of Public Administration Research and Theory", ("1053-1858", "1477-9803"), 1),
    Journal("PAR", "Public Administration Review", ("0033-3352", "1540-6210"), 1),
    Journal("PPMG", "Perspectives on Public Management and Governance", ("2398-4910", "2398-4929"), 1),
    Journal("JPAM", "Journal of Policy Analysis and Management", ("0276-8739", "1520-6688"), 1),
    Journal("AJPS", "American Journal of Political Science", ("0092-5853", "1540-5907"), 1),
    Journal("APSR", "American Political Science Review", ("0003-0554", "1537-5943"), 1),
    Journal("JOP", "The Journal of Politics", ("0022-3816", "1468-2508"), 1),
    Journal("PolAnalysis", "Political Analysis", ("1047-1987", "1476-4989"), 1),
    Journal("PMR", "Public Management Review", ("1471-9037", "1471-9045"), 2),
    Journal("PA", "Public Administration", ("0033-3298", "1467-9299"), 2),
    Journal("ARPA", "The American Review of Public Administration", ("0275-0740", "1552-3357"), 2),
    Journal("PSJ", "Policy Studies Journal", ("0190-292X", "1541-0072"), 2),
    Journal("IPMJ", "International Public Management Journal", ("1096-7494", "1559-3169"), 2),
    Journal("IJPA", "International Journal of Public Administration", ("0190-0692", "1532-4265"), 2),
    Journal("PolBeh", "Political Behavior", ("0190-9320", "1573-6687"), 2),
    Journal("PolPsych", "Political Psychology", ("0162-895X", "1467-9221"), 2),
    Journal("POQ", "Public Opinion Quarterly", ("0033-362X", "1537-5331"), 2),
    Journal("PolComm", "Political Communication", ("1058-4609", "1091-7675"), 2),
    Journal("PPMR", "Public Performance & Management Review", ("1530-9576", "1557-9271"), 3),
    Journal("GIQ", "Government Information Quarterly", ("0740-624X", "1872-9517"), 3),
    Journal("Governance", "Governance", ("0952-1895", "1468-0491"), 3),
    Journal("A&S", "Administration & Society", ("0095-3997", "1552-3039"), 3),
    Journal("ROPPA", "Review of Public Personnel Administration", ("0734-371X", "1552-759X"), 3),
    Journal("JAP", "Journal of Applied Psychology", ("0021-9010", "1939-1854"), 1),
    Journal("AMJ", "Academy of Management Journal", ("0001-4273", "1948-0989"), 1),
    Journal("AMR", "Academy of Management Review", ("0363-7425", "1930-3807"), 1),
    Journal("AMA", "Academy of Management Annals", ("1941-6520", "1941-6067"), 1),
    Journal("JOB", "Journal of Organizational Behavior", ("0894-3796", "1099-1379"), 2),
    Journal("JOM", "Journal of Management", ("0149-2063", "1557-1211"), 1),
    Journal("JPSP", "Journal of Personality and Social Psychology", ("0022-3514", "1939-1315"), 1),
    Journal("PSPB", "Personality and Social Psychology Bulletin", ("0146-1672", "1552-7433"), 2),
    Journal("MgmtSci", "Management Science", ("0025-1909", "1526-5501"), 1),
    Journal("MISQ", "MIS Quarterly", ("0276-7783", "2162-9730"), 1),
    Journal("ISR", "Information Systems Research", ("1047-7047", "1526-5536"), 1),
    Journal("SMJ", "Strategic Management Journal", ("0143-2095", "1097-0266"), 1),
    Journal("OrgSci", "Organization Science", ("1047-7039", "1526-5455"), 1),
    Journal("JBPA", "Journal of Behavioral Public Administration", ("2576-6465",), 2),
    Journal("JEPS", "Journal of Experimental Political Science", ("2052-2630", "2052-2649"), 2),
    Journal("OBHDP", "Organizational Behavior and Human Decision Processes", ("0749-5978", "1095-9920"), 1),
    Journal("NVSQ", "Nonprofit and Voluntary Sector Quarterly", ("0899-7640", "1552-7395"), 2),
)

JOURNAL_BY_NAME = {journal.name: journal for journal in JOURNALS}
JOURNAL_RANK = {journal.name: rank for rank, journal in enumerate(JOURNALS, start=1)}
JOURNAL_TIER = {journal.name: journal.tier for journal in JOURNALS}

# Fields group the newsletter into the reader's disciplines. The order here is
# the order of sections in the email; within a field, journals keep JOURNALS order.
FIELDS: tuple[str, ...] = ("행정·정책", "정치학", "경영·조직", "심리학", "정보시스템")
_FIELD_BY_SHORT = {
    **dict.fromkeys(
        ("JPART", "PAR", "PPMG", "JPAM", "PMR", "PA", "ARPA", "PSJ", "IPMJ", "IJPA",
         "PPMR", "GIQ", "Governance", "A&S", "ROPPA", "JBPA", "NVSQ"),
        "행정·정책",
    ),
    **dict.fromkeys(
        ("AJPS", "APSR", "JOP", "PolAnalysis", "PolBeh", "PolPsych", "POQ", "PolComm", "JEPS"), "정치학"
    ),
    **dict.fromkeys(("AMJ", "AMR", "AMA", "JOB", "JOM", "MgmtSci", "SMJ", "OrgSci", "OBHDP"), "경영·조직"),
    **dict.fromkeys(("JAP", "JPSP", "PSPB"), "심리학"),
    **dict.fromkeys(("MISQ", "ISR"), "정보시스템"),
}
JOURNAL_FIELD = {journal.name: _FIELD_BY_SHORT[journal.short_name] for journal in JOURNALS}
