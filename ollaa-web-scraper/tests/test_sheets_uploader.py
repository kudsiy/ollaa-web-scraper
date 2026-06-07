"""
Test script for Google Sheets Uploader.
Mocks gspread and credentials for verification.
"""
import unittest
from unittest.mock import MagicMock, patch, call
import os
import sys
import gspread

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from etl.sheets_uploader import SheetsUploader
from etl.sheets_exporter import UNIFIED_SCHEMA

class TestSheetsUploader(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.enabled = True
        self.mock_config.spreadsheet_id = "test_spreadsheet_id"
        self.mock_config.credentials_file = "test_credentials.json"
        self.mock_config.sheet_name = "Test Sheet"

    @patch('etl.sheets_uploader.Credentials')
    @patch('etl.sheets_uploader.gspread.authorize')
    @patch('etl.sheets_uploader.os.path.exists')
    def test_authenticate_success(self, mock_exists, mock_authorize, mock_credentials):
        mock_exists.return_value = True
        mock_creds_instance = MagicMock()
        mock_credentials.from_service_account_file.return_value = mock_creds_instance
        # Simulate service_account_email attribute
        mock_creds_instance.service_account_email = "test@test.iam.gserviceaccount.com"
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader._authenticate()
        
        self.assertTrue(result)
        mock_credentials.from_service_account_file.assert_called_once()
        mock_authorize.assert_called_once()

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._authenticate')
    def test_get_worksheet_new_sheet(self, mock_auth, mock_preflight):
        mock_auth.return_value = True
        mock_preflight.return_value = True
        uploader = SheetsUploader(self.mock_config)
        
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.col_count = 57
        mock_worksheet.row_values.return_value = []  # Empty headers
        
        uploader.client = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Simulate worksheet not found, then created
        import gspread
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet
        
        ws = uploader._get_worksheet()
        
        self.assertEqual(ws, mock_worksheet)
        mock_spreadsheet.add_worksheet.assert_called_once_with(
            title=self.mock_config.sheet_name, rows="100", cols="57"
        )
        # Should verify and update headers via _ensure_headers
        mock_worksheet.row_values.assert_called_once_with(1)
        mock_worksheet.update.assert_called_once_with(
            'A1:BE1', [UNIFIED_SCHEMA], value_input_option='RAW'
        )

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._authenticate')
    def test_get_worksheet_existing_with_wrong_headers(self, mock_auth, mock_preflight):
        mock_auth.return_value = True
        mock_preflight.return_value = True
        uploader = SheetsUploader(self.mock_config)
        
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.col_count = 57
        # Return incorrect headers
        mock_worksheet.row_values.return_value = ["wrong", "headers"]
        
        uploader.client = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        ws = uploader._get_worksheet()
        
        self.assertEqual(ws, mock_worksheet)
        mock_worksheet.row_values.assert_called_once_with(1)
        mock_worksheet.update.assert_called_once_with(
            'A1:BE1', [UNIFIED_SCHEMA], value_input_option='RAW'
        )

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._authenticate')
    def test_get_worksheet_existing_with_correct_headers(self, mock_auth, mock_preflight):
        mock_auth.return_value = True
        mock_preflight.return_value = True
        uploader = SheetsUploader(self.mock_config)
        
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.col_count = 57
        mock_worksheet.row_values.return_value = list(UNIFIED_SCHEMA)  # Correct headers
        
        uploader.client = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        ws = uploader._get_worksheet()
        
        self.assertEqual(ws, mock_worksheet)
        mock_worksheet.row_values.assert_called_once_with(1)
        # update should NOT be called when headers are already correct
        mock_worksheet.update.assert_not_called()

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._get_worksheet')
    def test_upload_listings(self, mock_get_ws, mock_preflight):
        mock_preflight.return_value = True
        mock_ws = MagicMock()
        mock_ws.col_values.return_value = []  # No existing hashes
        mock_ws.col_values.return_value = []  # No existing hashes (col A too)
        mock_get_ws.return_value = mock_ws
        
        uploader = SheetsUploader(self.mock_config)
        
        test_listings = [
            {"title": "Test Property", "price": 1000000, "source_name": "Test Source"}
        ]
        
        result = uploader.upload_listings(test_listings)
        
        self.assertTrue(result)
        # Should check for existing hashes (col 57)
        mock_ws.col_values.assert_any_call(57)
        # Should update with RAW input option
        mock_ws.update.assert_called_once()
        args, kwargs = mock_ws.update.call_args
        # args should be (range_label, rows, value_input_option='RAW')
        self.assertEqual(kwargs.get('value_input_option'), 'RAW')
        rows = args[1]
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 57)

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._get_worksheet')
    def test_upload_listings_deduplication(self, mock_get_ws, mock_preflight):
        """Test that listings with existing content_hash are skipped."""
        mock_preflight.return_value = True
        mock_ws = MagicMock()
        # Simulate existing content hashes in the sheet
        existing_hash = "abcdef1234567890"
        def col_values_side_effect(col):
            if col == 57:
                return ["content_hash", existing_hash]
            return []  # col 1 (A) returns empty
        mock_ws.col_values.side_effect = col_values_side_effect
        mock_get_ws.return_value = mock_ws
        
        uploader = SheetsUploader(self.mock_config)
        
        test_listings = [
            {"title": "Existing Property", "content_hash": existing_hash, "source_name": "Source A"},
            {"title": "New Property", "content_hash": "new_hash_12345", "source_name": "Source B"},
            {"title": "No Hash Property", "source_name": "Source C"},
        ]
        
        result = uploader.upload_listings(test_listings)
        
        self.assertTrue(result)
        # Should check for existing hashes (col 57)
        mock_ws.col_values.assert_any_call(57)
        # Should update with only 2 rows (the new and the no-hash one)
        mock_ws.update.assert_called_once()
        args, kwargs = mock_ws.update.call_args
        self.assertEqual(kwargs.get('value_input_option'), 'RAW')
        rows = args[1]
        self.assertEqual(len(rows), 2, "Should upload 2 listings (1 new + 1 without hash), skipping the duplicate")

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._get_worksheet')
    def test_upload_listings_all_duplicates(self, mock_get_ws, mock_preflight):
        """Test that when all listings are duplicates, nothing is uploaded."""
        mock_preflight.return_value = True
        mock_ws = MagicMock()
        existing_hash = "duplicate_hash"
        def col_values_side_effect(col):
            if col == 57:
                return ["content_hash", existing_hash]
            return []
        mock_ws.col_values.side_effect = col_values_side_effect
        mock_get_ws.return_value = mock_ws
        
        uploader = SheetsUploader(self.mock_config)
        
        test_listings = [
            {"title": "Dup 1", "content_hash": existing_hash, "source_name": "Source A"},
            {"title": "Dup 2", "content_hash": existing_hash, "source_name": "Source B"},
        ]
        
        result = uploader.upload_listings(test_listings)
        
        self.assertTrue(result)
        # update should NOT be called since all are duplicates
        mock_ws.update.assert_not_called()

    @patch('etl.sheets_uploader.SheetsUploader.pre_flight_check')
    @patch('etl.sheets_uploader.SheetsUploader._get_worksheet')
    def test_upload_listings_empty(self, mock_get_ws, mock_preflight):
        """Test that empty listings list returns True without sheet interaction."""
        mock_preflight.return_value = True
        mock_ws = MagicMock()
        mock_get_ws.return_value = mock_ws
        
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader.upload_listings([])
        
        self.assertTrue(result)
        mock_ws.col_values.assert_not_called()
        mock_ws.update.assert_not_called()

    @patch('etl.sheets_uploader.SheetsUploader._authenticate')
    @patch('etl.sheets_uploader.os.path.exists')
    def test_pre_flight_check_failure_no_creds(self, mock_exists, mock_auth):
        """Test pre-flight check fails when credentials file missing."""
        mock_exists.return_value = False
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader.pre_flight_check()
        
        self.assertFalse(result)

    @patch('etl.sheets_uploader.Credentials')
    @patch('etl.sheets_uploader.gspread.authorize')
    @patch('etl.sheets_uploader.os.path.exists')
    def test_pre_flight_check_success(self, mock_exists, mock_authorize, mock_credentials):
        """Test pre-flight check passes with valid credentials and spreadsheet."""
        mock_exists.return_value = True
        mock_creds_instance = MagicMock()
        mock_credentials.from_service_account_file.return_value = mock_creds_instance
        
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Test Sheet"
        mock_worksheet = MagicMock()
        mock_worksheet.row_count = 10
        mock_worksheet.col_count = 57
        
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_authorize.return_value = mock_client
        
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader.pre_flight_check()
        
        self.assertTrue(result)
        mock_client.open_by_key.assert_called_once_with(self.mock_config.spreadsheet_id)

    @patch('etl.sheets_uploader.Credentials')
    @patch('etl.sheets_uploader.gspread.authorize')
    @patch('etl.sheets_uploader.os.path.exists')
    def test_pre_flight_check_spreadsheet_not_found(self, mock_exists, mock_authorize, mock_credentials):
        """Test pre-flight check fails when spreadsheet is not accessible."""
        mock_exists.return_value = True
        mock_creds_instance = MagicMock()
        mock_credentials.from_service_account_file.return_value = mock_creds_instance
        
        mock_client = MagicMock()
        mock_client.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound("Spreadsheet not found")
        mock_authorize.return_value = mock_client
        
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader.pre_flight_check()
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()