"""
No automatic deletion (task W4): old listings are price history. The code never deletes
rows from the database or data from the Google Sheet; deleting is a manual step for the
owner, after a backup. Nothing here connects to the database or to Google.
"""
import pathlib
import re
from unittest.mock import MagicMock, patch

import schedule

from etl.db_writer import DBWriter
from etl.sheets_exporter import UNIFIED_SCHEMA
from etl.sheets_uploader import SheetsUploader

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {"venv", ".venv", "site-packages", "__pycache__", ".pytest_cache"}
DELETING = re.compile(
    r"\bdelete\s+from\b|\btruncate\b|\bdrop\s+(table|schema|database|view|index)\b"
    r"|\.(delete_rows|delete_columns|batch_clear|values_clear|del_worksheet)\(",
    re.IGNORECASE,
)


def test_no_code_deletes_data():
    for path in PROJECT_DIR.rglob("*.py"):
        if path.name == "test_no_deletion.py" or SKIP_DIRS & set(path.parts):
            continue
        match = DELETING.search(path.read_text(encoding="utf-8"))
        assert not match, f"Deleting code in {path.relative_to(PROJECT_DIR)}: {match.group(0)}"


def test_database_writer_has_no_delete():
    assert not hasattr(DBWriter, "delete_old_listings")


def test_scheduler_only_scrapes():
    from scheduler import ScraperScheduler

    schedule.clear()
    try:
        ScraperScheduler()._register_scheduled_jobs()
        jobs = schedule.get_jobs()
        assert {job.job_func.func.__name__ for job in jobs} == {"_run_scraper_group"}
        assert {job.job_func.args[0] for job in jobs} == {"banks", "tenders", "listings"}
    finally:
        schedule.clear()


def _uploader_with_sheet(col_count, headers):
    config = MagicMock(enabled=True, spreadsheet_id="test_spreadsheet_id",
                       credentials_file="test_credentials.json", sheet_name="Test Sheet")
    uploader = SheetsUploader(config)
    worksheet = MagicMock(col_count=col_count)
    worksheet.row_values.return_value = headers
    uploader.client = MagicMock()
    uploader.client.open_by_key.return_value.worksheet.return_value = worksheet
    return uploader, worksheet


@patch("etl.sheets_uploader.SheetsUploader._authenticate", return_value=True)
def test_sheet_with_extra_columns_is_never_shrunk(_auth):
    uploader, worksheet = _uploader_with_sheet(60, list(UNIFIED_SCHEMA) + ["owner notes"])
    assert uploader._get_worksheet() is worksheet
    worksheet.resize.assert_not_called()
    worksheet.update.assert_not_called()


@patch("etl.sheets_uploader.SheetsUploader._authenticate", return_value=True)
def test_small_sheet_still_grows_to_57_columns(_auth):
    uploader, worksheet = _uploader_with_sheet(26, [])
    uploader._get_worksheet()
    worksheet.resize.assert_called_once_with(cols=57)
