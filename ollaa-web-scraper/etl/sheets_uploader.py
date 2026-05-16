"""
Google Sheets Uploader for property data.
Authenticates via service account and appends rows to a live Google Sheet.
"""
import logging
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
import os

from config import get_config
from etl.sheets_exporter import SheetsExporter, UNIFIED_SCHEMA

logger = logging.getLogger(__name__)

class SheetsUploader:
    """
    Uploader class to push property data to Google Sheets.
    """
    def __init__(self, config=None):
        self.config = config or get_config().sheets
        self.exporter = SheetsExporter()
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

    def _authenticate(self) -> bool:
        """Authenticate with Google Sheets API."""
        if self.client:
            return True

        if not self.config.enabled:
            logger.warning("Google Sheets upload is disabled.")
            return False

        if not os.path.exists(self.config.credentials_file):
            logger.error(f"Google Sheets credentials file not found: {self.config.credentials_file}")
            return False

        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_file(
                self.config.credentials_file,
                scopes=scopes
            )
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return False

    def _get_worksheet(self):
        """Get or create the worksheet."""
        if self.worksheet:
            return self.worksheet

        if not self._authenticate():
            return None

        try:
            self.spreadsheet = self.client.open_by_key(self.config.spreadsheet_id)
            try:
                self.worksheet = self.spreadsheet.worksheet(self.config.sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"Worksheet '{self.config.sheet_name}' not found. Creating it.")
                self.worksheet = self.spreadsheet.add_worksheet(title=self.config.sheet_name, rows="100", cols="57")
            
            # Check if sheet is empty and needs headers
            if not self.worksheet.get_all_values():
                logger.info("Sheet is empty. Adding headers.")
                self.worksheet.append_row(UNIFIED_SCHEMA)
            
            return self.worksheet
        except Exception as e:
            logger.error(f"Failed to access Google Sheet: {e}")
            return None

    def upload_listings(self, listings: List[Dict[str, Any]]) -> bool:
        """
        Upload a list of normalized listings to Google Sheets.
        """
        if not listings:
            return True

        worksheet = self._get_worksheet()
        if not worksheet:
            return False

        try:
            formatted_listings = [self.exporter.format_listing(l) for l in listings]
            rows_to_append = []
            for listing in formatted_listings:
                row = [listing.get(col) for col in UNIFIED_SCHEMA]
                rows_to_append.append(row)

            worksheet.append_rows(rows_to_append)
            logger.info(f"Successfully uploaded {len(rows_to_append)} rows to Google Sheet.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload rows to Google Sheet: {e}")
            return False
