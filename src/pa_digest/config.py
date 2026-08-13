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
)

JOURNAL_BY_NAME = {journal.name: journal for journal in JOURNALS}
JOURNAL_RANK = {journal.name: rank for rank, journal in enumerate(JOURNALS, start=1)}
JOURNAL_TIER = {journal.name: journal.tier for journal in JOURNALS}
