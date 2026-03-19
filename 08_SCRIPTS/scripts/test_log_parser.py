import unittest
import os
import sys
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO
from unittest.mock import patch, mock_open

# Adjust the path to import from the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import log_parser

class TestLogParser(unittest.TestCase):

    def setUp(self):
        # Reset DB_PATH for each test to ensure isolation, especially important if any db.py call were to happen
        # but in this specific module test, db.py is not imported so this is defensive.
        if hasattr(log_parser, 'db') and hasattr(log_parser.db, 'DB_PATH'):
            self.original_db_path = log_parser.db.DB_PATH
            log_parser.db.DB_PATH = ":memory:"
            # Ensure the test database is initialized if db module is used by log_parser
            log_parser.db.init_db()

        # Define common timestamps for testing filters
        self.dt_format = log_parser.TIMESTAMP_FORMAT
        self.t1 = datetime.strptime("2023-01-01 10:00:00", self.dt_format)
        self.t2 = datetime.strptime("2023-01-01 11:00:00", self.dt_format)
        self.t3 = datetime.strptime("2023-01-01 12:00:00", self.dt_format)

    def tearDown(self):
        # Restore DB_PATH if it was modified
        if hasattr(log_parser, 'db') and hasattr(log_parser.db, 'DB_PATH'):
            log_parser.db.DB_PATH = self.original_db_path
            # Close any open test database connections if db module is used
            log_parser.db.close_all_connections()


    # --- Test parse_log_entry ---
    def test_parse_log_entry_valid(self):
        line = "[2023-10-26 10:00:00] [ERROR] [ERR-404] Page not found."
        entry = log_parser.parse_log_entry(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['timestamp'], "2023-10-26 10:00:00")
        self.assertEqual(entry['level'], "ERROR")
        self.assertEqual(entry['error_code'], "ERR-404")
        self.assertEqual(entry['message'], "Page not found.")

    def test_parse_log_entry_valid_no_error_code(self):
        line = "[2023-10-26 10:00:00] [INFO] User logged in."
        entry = log_parser.parse_log_entry(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['timestamp'], "2023-10-26 10:00:00")
        self.assertEqual(entry['level'], "INFO")
        self.assertIsNone(entry['error_code']) # Should be None if not present
        self.assertEqual(entry['message'], "User logged in.")

    def test_parse_log_entry_malformed(self):
        line = "This is not a log entry."
        entry = log_parser.parse_log_entry(line)
        self.assertIsNone(entry)

        line = "[2023/10/26 10:00:00] [ERROR] Message" # Wrong timestamp format
        entry = log_parser.parse_log_entry(line)
        self.assertIsNone(entry)

    def test_parse_log_entry_empty_message(self):
        line = "[2023-10-26 10:00:00] [WARN] [WARN-001]"
        entry = log_parser.parse_log_entry(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['error_code'], "WARN-001")
        self.assertEqual(entry['message'], "") # Empty message should be handled

    def test_parse_log_entry_different_level(self):
        line = "[2023-11-01 09:30:15] [DEBUG] Debug information."
        entry = log_parser.parse_log_entry(line)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['level'], "DEBUG")
        self.assertIsNone(entry['error_code'])


    # --- Test is_within_time_range ---
    def test_is_within_time_range_all_none(self):
        self.assertTrue(log_parser.is_within_time_range(self.t2.strftime(self.dt_format), None, None))

    def test_is_within_time_range_only_start(self):
        self.assertTrue(log_parser.is_within_time_range(self.t2.strftime(self.dt_format), self.t1, None))
        self.assertFalse(log_parser.is_within_time_range(self.t1.strftime(self.dt_format), self.t2, None))

    def test_is_within_time_range_only_end(self):
        self.assertTrue(log_parser.is_within_time_range(self.t2.strftime(self.dt_format), None, self.t3))
        self.assertFalse(log_parser.is_within_time_range(self.t3.strftime(self.dt_format), None, self.t2))

    def test_is_within_time_range_both(self):
        self.assertTrue(log_parser.is_within_time_range(self.t2.strftime(self.dt_format), self.t1, self.t3))
        self.assertFalse(log_parser.is_within_time_range(self.t1.strftime(self.dt_format), self.t2, self.t3))
        self.assertFalse(log_parser.is_within_time_range(self.t3.strftime(self.dt_format), self.t1, self.t2))

    def test_is_within_time_range_malformed_timestamp(self):
        with self.assertLogs('root', level='WARNING') as cm:
            result = log_parser.is_within_time_range("malformed-time", self.t1, self.t3)
            self.assertFalse(result)
            self.assertIn("Malformed timestamp", cm.output[0])


    # --- Test matches_error_codes ---
    def test_matches_error_codes_empty_target(self):
        self.assertTrue(log_parser.matches_error_codes("ERR-404", set()))
        self.assertTrue(log_parser.matches_error_codes("WARN-001", set()))

    def test_matches_error_codes_case_insensitive(self):
        self.assertTrue(log_parser.matches_error_codes("err-404", {"ERR-404"}))
        self.assertTrue(log_parser.matches_error_codes("warn-500", {"WARN-500", "ERR-100"}))

    def test_matches_error_codes_no_match(self):
        self.assertFalse(log_parser.matches_error_codes("ERR-404", {"ERR-500"}))
        self.assertFalse(log_parser.matches_error_codes("INFO-001", {"WARN-001"}))

    def test_matches_error_codes_none_error_code(self):
        self.assertFalse(log_parser.matches_error_codes(None, {"ERR-404"}))
        self.assertTrue(log_parser.matches_error_codes(None, set())) # No target codes, so should pass if error_code is None. (No, the logic says if target_codes empty, then any error_code from log is a match. If error_code is None, then it's not an error code.)

    def test_matches_error_codes_none_error_code_with_empty_target(self):
        # If target_codes is empty, it means "extract all errors".
        # If the log line has no error code (parsed_entry['error_code'] is None), it's not an error.
        self.assertFalse(log_parser.matches_error_codes(None, set()))


    # --- Test process_log_file ---
    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.info') # Mock logging.info to suppress output during tests
    @patch('log_parser.logging.warning') # Mock logging.warning to suppress output during tests
    @patch('log_parser.logging.debug') # Mock logging.debug to suppress output during tests
    def test_process_log_file_basic(self, mock_debug, mock_warn, mock_info, mock_file_open):
        log_content = (
            "[2023-10-26 10:00:00] [ERROR] [ERR-404] Page not found.\n"
            "[2023-10-26 10:01:00] [INFO] User logged in.\n"
            "[2023-10-26 10:02:00] [WARN] [WARN-001] Deprecation notice.\n"
            "[2023-10-26 10:03:00] [ERROR] [ERR-500] Server crash.\n"
        )
        mock_file_open.return_value = StringIO(log_content)

        # Mock argparse.Namespace
        class MockArgs:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.error_codes = [] # Empty means extract all with error codes

        extracted = log_parser.process_log_file(
            Path("dummy.log"),
            set(), # No target codes, so all error codes
            None, None
        )
        self.assertEqual(len(extracted), 3)
        self.assertEqual(extracted[0]['error_code'], "ERR-404")
        self.assertEqual(extracted[1]['error_code'], "WARN-001")
        self.assertEqual(extracted[2]['error_code'], "ERR-500")

    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.info')
    @patch('log_parser.logging.warning')
    @patch('log_parser.logging.debug')
    def test_process_log_file_with_filters(self, mock_debug, mock_warn, mock_info, mock_file_open):
        log_content = (
            "[2023-10-26 10:00:00] [ERROR] [ERR-404] Page not found.\n"
            "[2023-10-26 10:01:00] [INFO] User logged in.\n"
            "[2023-10-26 10:02:00] [WARN] [WARN-001] Deprecation notice.\n"
            "[2023-10-26 10:03:00] [ERROR] [ERR-500] Server crash.\n"
            "[2023-10-26 10:04:00] [ERROR] [ERR-404] Another 404.\n"
        )
        mock_file_open.return_value = StringIO(log_content)

        start_time = datetime.strptime("2023-10-26 10:01:30", self.dt_format)
        end_time = datetime.strptime("2023-10-26 10:03:30", self.dt_format)
        target_codes = {"ERR-500", "WARN-001"}

        extracted = log_parser.process_log_file(
            Path("dummy.log"),
            target_codes,
            start_time, end_time
        )
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]['error_code'], "WARN-001")
        self.assertEqual(extracted[1]['error_code'], "ERR-500")
        self.assertEqual(extracted[0]['timestamp'], "2023-10-26 10:02:00")
        self.assertEqual(extracted[1]['timestamp'], "2023-10-26 10:03:00")

    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.info')
    @patch('log_parser.logging.warning')
    @patch('log_parser.logging.debug')
    def test_process_log_file_malformed_lines(self, mock_debug, mock_warn, mock_info, mock_file_open):
        log_content = (
            "[2023-10-26 10:00:00] [ERROR] [ERR-404] Valid.\n"
            "Malformed line 1\n"
            "[2023-10-26 10:01:00] Invalid format here\n"
            "[2023-10-26 10:02:00] [WARN] [WARN-001] Valid.\n"
        )
        mock_file_open.return_value = StringIO(log_content)
        
        extracted = log_parser.process_log_file(
            Path("dummy.log"), set(), None, None
        )
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]['error_code'], "ERR-404")
        self.assertEqual(extracted[1]['error_code'], "WARN-001")
        mock_debug.assert_any_call(self.anything_containing("Skipping malformed line"))

    # Helper for asserting log messages containing specific text
    def anything_containing(self, text):
        class AnyStringContaining(str):
            def __eq__(self, other):
                return text in other
        return AnyStringContaining(text)


    # --- Test write_csv_summary ---
    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.info')
    @patch('log_parser.logging.error')
    def test_write_csv_summary_success(self, mock_error, mock_info, mock_file_open):
        data = [
            {'timestamp': '2023-10-26 10:00:00', 'error_code': 'ERR-404', 'message': 'Not Found'},
            {'timestamp': '2023-10-26 10:01:00', 'error_code': 'WARN-001', 'message': 'Warning'}
        ]
        output_path = Path("output.csv")

        log_parser.write_csv_summary(output_path, data)
        mock_file_open.assert_called_once_with(output_path, 'w', newline='', encoding='utf-8')
        handle = mock_file_open()
        # Check that header and rows are written. StringIO captures content written.
        written_content = handle.write.call_args_list
        # The first call is the header, subsequent calls are rows.
        # This is a bit brittle, often better to mock csv.writer directly
        # or assert on the parsed CSV output of mock_file_open.
        
        # A more robust check: parse the written content
        csv_output = "".join([call.args[0] for call in written_content])
        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['timestamp'], '2023-10-26 10:00:00')
        self.assertEqual(rows[0]['error_code'], 'ERR-404')

        mock_info.assert_called_with(f"Successfully wrote summary to {output_path}")

    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.info')
    def test_write_csv_summary_no_data(self, mock_info, mock_file_open):
        data = []
        output_path = Path("output.csv")
        log_parser.write_csv_summary(output_path, data)
        mock_file_open.assert_not_called() # Should not open file if no data
        mock_info.assert_called_with(f"No data to write to {output_path}. Skipping CSV creation.")

    @patch('builtins.open', new_callable=mock_open)
    @patch('log_parser.logging.error')
    def test_write_csv_summary_io_error(self, mock_error, mock_file_open):
        mock_file_open.side_effect = IOError("Permission denied")
        data = [{'timestamp': '2023-10-26 10:00:00', 'error_code': 'ERR-404', 'message': 'Not Found'}]
        output_path = Path("non_writable.csv")

        log_parser.write_csv_summary(output_path, data)
        mock_error.assert_called_with(self.anything_containing("Error writing to CSV file"))

    # --- Test main function (integration style) ---
    @patch('log_parser.process_log_file')
    @patch('log_parser.write_csv_summary')
    @patch('log_parser.logging.info')
    @patch('log_parser.logging.error')
    @patch('log_parser.Path.is_file', return_value=True)
    def test_main_function_full_flow(
        self, mock_is_file, mock_error_log, mock_info_log, 
        mock_write_csv, mock_process_file
    ):
        # Mocking process_log_file to return some data
        mock_process_file.return_value = [
            {'timestamp': '2023-10-26 10:00:00', 'error_code': 'ERR-404', 'message': 'Test Message 1'},
            {'timestamp': '2023-10-26 10:01:00', 'error_code': 'WARN-001', 'message': 'Test Message 2'}
        ]

        # Simulate command line arguments
        test_args = [
            "log_parser.py",
            "log1.log", "log2.log",
            "--output-csv", "summary.csv",
            "--start-time", "2023-10-26 09:00:00",
            "--end-time", "2023-10-26 11:00:00",
            "--error-codes", "ERR-404", "WARN-001",
            "--verbose"
        ]

        with patch.object(sys, 'argv', test_args):
            log_parser.main()

        # Assertions
        self.assertEqual(mock_process_file.call_count, 2) # Called for log1.log and log2.log
        mock_write_csv.assert_called_once()
        self.assertGreater(mock_info_log.call_count, 0)
        mock_error_log.assert_not_called()

    @patch('log_parser.logging.error')
    @patch('log_parser.Path.is_file', return_value=True)
    @patch('sys.exit') # Mock sys.exit to prevent script from exiting
    def test_main_function_invalid_timestamp_exit(self, mock_exit, mock_is_file, mock_error_log):
        test_args = [
            "log_parser.py",
            "log1.log",
            "--output-csv", "summary.csv",
            "--start-time", "invalid-time-format"
        ]
        with patch.object(sys, 'argv', test_args):
            log_parser.main()
        mock_error_log.assert_called_with(self.anything_containing("Invalid start time format"))
        # In actual usage sys.exit would be called, but we mock it.

    @patch('log_parser.process_log_file', return_value=[]) # No data extracted
    @patch('log_parser.write_csv_summary')
    @patch('log_parser.logging.info')
    @patch('log_parser.Path.is_file', return_value=True)
    def test_main_function_no_matching_entries(self, mock_is_file, mock_info_log, mock_write_csv, mock_process_file):
        test_args = [
            "log_parser.py",
            "log1.log",
            "--output-csv", "summary.csv"
        ]
        with patch.object(sys, 'argv', test_args):
            log_parser.main()
        
        mock_process_file.assert_called_once()
        mock_write_csv.assert_not_called() # Should not write if no data
        mock_info_log.assert_called_with("No matching error entries found across all log files.")


if __name__ == '__main__':
    unittest.main()
