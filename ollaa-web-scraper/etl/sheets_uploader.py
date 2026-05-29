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
            # Log the service account email for diagnostics
            if hasattr(credentials, 'service_account_email'):
                logger.info(f"Authenticated with service account: {credentials.service_account_email}")
            elif credentials._service_account_email:
                logger.info(f"Authenticated with service account: {credentials._service_account_email}")
            else:
                # Try to extract from the credentials file
                try:
                    import json
                    with open(self.config.credentials_file, 'r') as f:
                        creds_data = json.load(f)
                    sa_email = creds_data.get('client_email', 'unknown')
                    logger.info(f"Authenticated with service account: {sa_email}")
                except Exception:
                    logger.info("Authenticated with service account (email not extractable)")
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return False

    def _get_worksheet(self):
        """Get or create the worksheet with verified headers and correct column count."""
        if self.worksheet:
            return self.worksheet

        if not self._authenticate():
            return None

        try:
            logger.info(f"Opening spreadsheet with ID: {self.config.spreadsheet_id}")
            self.spreadsheet = self.client.open_by_key(self.config.spreadsheet_id)
            logger.info(f"Successfully opened spreadsheet: '{self.spreadsheet.title}' (ID: {self.config.spreadsheet_id})")
            sheet_name = self.config.sheet_name
            if not sheet_name or sheet_name == "Property Data":
                sheet_name = "Sheet1"
            try:
                self.worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"Found existing worksheet: '{sheet_name}'")
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"Worksheet '{sheet_name}' not found. Creating it.")
                self.worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="57")

            # Ensure sheet has exactly 57 columns for the unified schema
            if self.worksheet.col_count != 57:
                logger.info(f"Sheet has {self.worksheet.col_count} columns. Resizing to 57.")
                self.worksheet.resize(cols=57)

            # Verify and fix headers in row 1
            self._ensure_headers()

            return self.worksheet
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet not found with ID: {self.config.spreadsheet_id}. "
                         f"Ensure the service account has been granted access to this sheet.")
            return None
        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error accessing spreadsheet {self.config.spreadsheet_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to access Google Sheet (ID: {self.config.spreadsheet_id}): {e}")
            return None

    def _ensure_headers(self):
        """Ensure row 1 contains the exact 57-column UNIFIED_SCHEMA headers."""
        try:
            # Force refresh to ensure we have latest headers
            existing_headers = self.worksheet.row_values(1)
        except Exception:
            existing_headers = []

        # Force match check: if length or content doesn't match UNIFIED_SCHEMA
        if len(existing_headers) != 57 or existing_headers != list(UNIFIED_SCHEMA):
            logger.info(f"Headers do not match UNIFIED_SCHEMA (found {len(existing_headers)} cols). Overwriting immediately.")
            self.worksheet.update('A1:BE1', [UNIFIED_SCHEMA], value_input_option='RAW')
            logger.info("Headers updated successfully.")
        else:
            logger.debug("Headers verified and match UNIFIED_SCHEMA.")

    def pre_flight_check(self) -> bool:
        """
        Pre-flight check to verify Google Sheet accessibility before processing listings.
        Returns True if the sheet is accessible and writable, False otherwise.
        """
        logger.info("Running pre-flight check for Google Sheets access...")
        if not self.config.enabled:
            logger.warning("Pre-flight: Google Sheets upload is disabled.")
            return False

        if not os.path.exists(self.config.credentials_file):
            logger.error(f"Pre-flight: Credentials file not found: {self.config.credentials_file}")
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

            # Log service account email
            sa_email = "unknown"
            try:
                import json
                with open(self.config.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                sa_email = creds_data.get('client_email', 'unknown')
            except Exception:
                pass
            logger.info(f"Pre-flight: Service account email: {sa_email}")

            client = gspread.authorize(credentials)
            logger.info(f"Pre-flight: Attempting to open spreadsheet ID: {self.config.spreadsheet_id}")
            spreadsheet = client.open_by_key(self.config.spreadsheet_id)
            logger.info(f"Pre-flight: Successfully opened spreadsheet '{spreadsheet.title}' (ID: {self.config.spreadsheet_id})")

            # Try to access the worksheet
            sheet_name = self.config.sheet_name
            if not sheet_name or sheet_name == "Property Data":
                sheet_name = "Sheet1"
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"Pre-flight: Found worksheet '{sheet_name}' with {worksheet.row_count} rows and {worksheet.col_count} cols")
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"Pre-flight: Worksheet '{sheet_name}' not found (will be created during upload).")
                pass

            logger.info("Pre-flight check PASSED - Google Sheet is accessible and writable.")
            return True

        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Pre-flight FAILED: Spreadsheet not found with ID: {self.config.spreadsheet_id}. "
                         f"Grant access to '{sa_email}' if not already done.")
            return False
        except gspread.exceptions.APIError as e:
            logger.error(f"Pre-flight FAILED: Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Pre-flight FAILED: {e}")
            return False

    def upload_listings(self, listings: List[Dict[str, Any]]) -> bool:
        """
        Upload a list of normalized listings to Google Sheets.
        Performs sheet-level deduplication using content_hash.
        """
        if not listings:
            logger.info("No listings to upload.")
            return True

        # Pre-flight check before proceeding
        if not self.pre_flight_check():
            logger.error("Pre-flight check failed. Aborting upload.")
            return False

        worksheet = self._get_worksheet()
        if not worksheet:
            return False

        try:
            # Sheet-level deduplication: fetch existing content_hashes from column 57
            existing_hashes = set()
            try:
                hash_values = worksheet.col_values(57)
                # Skip header row (index 0) and any empty values
                existing_hashes = set(h for h in hash_values[1:] if h)
                if existing_hashes:
                    logger.info(f"Found {len(existing_hashes)} existing content hashes in sheet")
            except Exception as e:
                logger.warning(f"Could not fetch existing content hashes from sheet: {e}")

            # Filter out listings that already exist in the sheet
            filtered_listings = []
            duplicate_count = 0
            for l in listings:
                content_hash = l.get("content_hash")
                if content_hash and content_hash in existing_hashes:
                    duplicate_count += 1
                else:
                    filtered_listings.append(l)

            if duplicate_count > 0:
                logger.info(f"Skipped {duplicate_count} duplicate listing(s) already present in the sheet")
            logger.info(f"Upload stats: {len(filtered_listings)} new rows, {duplicate_count} duplicates skipped out of {len(listings)} total")

            if not filtered_listings:
                logger.info("All listings are duplicates. Nothing to upload.")
                return True

            formatted_listings = [self.exporter.format_listing(l) for l in filtered_listings]
            rows_to_append = []
            for listing in formatted_listings:
                row = [listing.get(col) for col in UNIFIED_SCHEMA]
                rows_to_append.append(row)

            # Logic to find the first empty row in Column A to prevent auto-formatting/indenting
            # Replacement for worksheet.append_rows
            col_a = worksheet.col_values(1)
            first_empty_row = len(col_a) + 1
            
            # Calculate range: A{row}:BE{row+N}
            last_row = first_empty_row + len(rows_to_append) - 1
            range_label = f"A{first_empty_row}:BE{last_row}"
            
            logger.info(f"Updating range {range_label} with {len(rows_to_append)} rows using RAW input")
            worksheet.update(range_label, rows_to_append, value_input_option='RAW')
            logger.info(f"Successfully uploaded {len(rows_to_append)} rows to Google Sheet (spreadsheet ID: {self.config.spreadsheet_id}).")
            return True
        except Exception as e:
            logger.error(f"Failed to upload rows to Google Sheet: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    import json
    import os
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uploader = SheetsUploader()
    json_file = "property_data.json"
    
    if os.path.exists(json_file):
        logger.info(f"Reading listings from {json_file}")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                listings = json.load(f)
            logger.info(f"Found {len(listings)} listings. Starting upload...")
            uploader.upload_listings(listings)
        except Exception as e:
            logger.error(f"Error during standalone upload: {e}")
    else:
        logger.error(f"JSON file {json_file} not found. Run unified_exporter.py first.")