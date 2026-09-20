from datetime import date

from openpyxl import load_workbook

from pa_digest.archive import HEADERS, export_archive
from pa_digest.models import Article
from pa_digest.state import StateStore


def test_export_archive_includes_requested_columns_and_title_link(tmp_path) -> None:
    state = StateStore(tmp_path / "state.json")
    article = Article(
        doi="10.1234/example",
        title="An Example Article",
        journal="Governance",
        journal_short="Governance",
        authors=["Jane Doe"],
        publication_date=date(2026, 8, 5),
        url="https://doi.org/10.1234/example",
        abstract="English abstract.",
        summary_ko="한국어 요약.",
        method="서베이",
        method_detail="패널 설문",
        constructs=["Trust", "Governance"],
    )
    state.prepare("batch", "key", [article], "2026-08-07T00:00:00+00:00")
    output = tmp_path / "archive.xlsx"
    export_archive(state, output)

    sheet = load_workbook(output).active
    assert [cell.value for cell in sheet[1]] == HEADERS
    assert sheet["A2"].value == "Jane Doe"
    assert sheet["J2"].value == "English abstract."
    assert sheet["C2"].hyperlink.target == "https://doi.org/10.1234/example"
