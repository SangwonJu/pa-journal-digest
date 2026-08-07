from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Journal:
    short_name: str
    name: str
    issns: tuple[str, ...]

    @property
    def primary_issn(self) -> str:
        return self.issns[0]


JOURNALS: tuple[Journal, ...] = (
    Journal("JPART", "Journal of Public Administration Research and Theory", ("1053-1858", "1477-9803")),
    Journal("PAR", "Public Administration Review", ("0033-3352", "1540-6210")),
    Journal("ARPA", "The American Review of Public Administration", ("0275-0740", "1552-3357")),
    Journal("PMR", "Public Management Review", ("1471-9037", "1471-9045")),
    Journal("IPMJ", "International Public Management Journal", ("1096-7494", "1559-3169")),
    Journal("PA", "Public Administration", ("0033-3298", "1467-9299")),
    Journal("Governance", "Governance", ("0952-1895", "1468-0491")),
    Journal("A&S", "Administration & Society", ("0095-3997", "1552-3039")),
    Journal("PPMG", "Perspectives on Public Management and Governance", ("2398-4910", "2398-4929")),
    Journal("PPMR", "Public Performance & Management Review", ("1530-9576", "1557-9271")),
    Journal("GIQ", "Government Information Quarterly", ("0740-624X", "1872-9517")),
    Journal("PSJ", "Policy Studies Journal", ("0190-292X", "1541-0072")),
    Journal("ROPPA", "Review of Public Personnel Administration", ("0734-371X", "1552-759X")),
)

JOURNAL_BY_NAME = {journal.name: journal for journal in JOURNALS}

