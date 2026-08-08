from pathlib import Path


def test_daily_schedule_is_830_eastern() -> None:
    workflow = Path(".github/workflows/daily-digest.yml").read_text(encoding="utf-8")

    assert 'cron: "30 8 * * *"' in workflow
    assert 'timezone: "America/New_York"' in workflow
