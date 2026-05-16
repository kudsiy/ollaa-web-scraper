"""
Test script for Google Sheets Uploader.
Mocks gspread and credentials for verification.
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

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
        uploader = SheetsUploader(self.mock_config)
        
        result = uploader._authenticate()
        
        self.assertTrue(result)
        mock_credentials.from_service_account_file.assert_called_once()
        mock_authorize.assert_called_once()

    @patch('etl.sheets_uploader.SheetsUploader._authenticate')
    def test_get_worksheet_new_sheet(self, mock_auth):
        mock_auth.return_value = True
        uploader = SheetsUploader(self.mock_config)
        
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        
        uploader.client = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Simulate worksheet not found, then created
        import gspread
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet
        
        # Mock empty sheet
        mock_worksheet.get_all_values.return_value = []
        
        ws = uploader._get_worksheet()
        
        self.assertEqual(ws, mock_worksheet)
        mock_spreadsheet.add_worksheet.assert_called_once_with(title=self.mock_config.sheet_name, rows="100", cols="57")
        mock_worksheet.append_row.assert_called_once_with(UNIFIED_SCHEMA)

    @patch('etl.sheets_uploader.SheetsUploader._get_worksheet')
    def test_upload_listings(self, mock_get_ws):
        mock_ws = MagicMock()
        mock_get_ws.return_value = mock_ws
        
        uploader = SheetsUploader(self.mock_config)
        
        test_listings = [
            {"title": "Test Property", "price": 1000000, "source_name": "Test Source"}
        ]
        
        result = uploader.upload_listings(test_listings)
        
        self.assertTrue(result)
        mock_ws.append_rows.assert_called_once()
        rows = mock_ws.append_rows.call_args[0][0]
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 57)

if __name__ == '__main__':
    unittest.main()
