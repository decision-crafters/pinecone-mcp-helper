"""
Unit tests for the Repomix execution and output processing module.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import xml.etree.ElementTree as ET

from repo_ingestion.repomix.processor import (
    check_repomix_installed, execute_repomix, parse_repomix_output,
    extract_urls_from_repomix_output
)


class TestRepomixProcessor(unittest.TestCase):
    """Test cases for the Repomix execution and output processing module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample Repomix output XML file
        self.xml_content = """
        <repomix>
            <file path="/path/to/file1.py">
                This is content of file1.py
                It contains a URL: https://example.com
            </file>
            <file path="/path/to/file2.py">
                This is content of file2.py
                It contains multiple URLs:
                https://example.org
                http://test.com
            </file>
        </repomix>
        """
        
        self.xml_path = os.path.join(self.temp_dir.name, "repomix-output.xml")
        with open(self.xml_path, "w") as f:
            f.write(self.xml_content)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    @patch('subprocess.run')
    def test_check_repomix_installed(self, mock_run):
        """Test checking if Repomix is installed."""
        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Check if Repomix is installed
        self.assertTrue(check_repomix_installed())
        
        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            ["repomix", "--version"],
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
            check=False
        )
        
        # Mock subprocess.run to return failure
        mock_process.returncode = 1
        self.assertFalse(check_repomix_installed())
        
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(check_repomix_installed())

    @patch('subprocess.run')
    @patch('repo_ingestion.repomix.processor.check_repomix_installed')
    def test_execute_repomix(self, mock_check_installed, mock_run):
        """Test executing Repomix."""
        # Mock check_repomix_installed to return True
        mock_check_installed.return_value = True
        
        # Mock subprocess.run to return success
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Execute Repomix
        repo_path = "/path/to/repo"
        output_file = os.path.join(repo_path, "repomix-output.xml")
        result = execute_repomix(repo_path)
        
        # Verify result
        self.assertEqual(result, output_file)
        
        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            ["repomix", "--output", output_file],
            cwd=repo_path,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
            check=True
        )
        
        # Test with custom output file
        custom_output = "/path/to/custom/output.xml"
        result = execute_repomix(repo_path, custom_output)
        
        # Verify result
        self.assertEqual(result, custom_output)
        
        # Mock check_repomix_installed to return False
        mock_check_installed.return_value = False
        
        # Execute Repomix and expect FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            execute_repomix(repo_path)

    def test_parse_repomix_output(self):
        """Test parsing Repomix XML output."""
        # Parse Repomix output
        chunks = parse_repomix_output(self.xml_path)
        
        # Verify chunks
        self.assertEqual(len(chunks), 2)
        
        # Verify first chunk
        self.assertEqual(chunks[0]["source_type"], "repository")
        self.assertEqual(chunks[0]["file_path"], "/path/to/file1.py")
        self.assertIn("This is content of file1.py", chunks[0]["text"])
        self.assertIn("https://example.com", chunks[0]["text"])
        
        # Verify second chunk
        self.assertEqual(chunks[1]["source_type"], "repository")
        self.assertEqual(chunks[1]["file_path"], "/path/to/file2.py")
        self.assertIn("This is content of file2.py", chunks[1]["text"])
        self.assertIn("https://example.org", chunks[1]["text"])
        self.assertIn("http://test.com", chunks[1]["text"])
        
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            parse_repomix_output("/path/to/nonexistent/file.xml")
        
        # Test with invalid XML
        invalid_xml_path = os.path.join(self.temp_dir.name, "invalid.xml")
        with open(invalid_xml_path, "w") as f:
            f.write("<invalid>")
        
        with self.assertRaises(ET.ParseError):
            parse_repomix_output(invalid_xml_path)

    def test_extract_urls_from_repomix_output(self):
        """Test extracting URLs from Repomix XML output."""
        # Extract URLs
        urls = extract_urls_from_repomix_output(self.xml_path)
        
        # Verify URLs
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example.com", urls)
        self.assertIn("https://example.org", urls)
        self.assertIn("http://test.com", urls)
        
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            extract_urls_from_repomix_output("/path/to/nonexistent/file.xml")
        
        # Test with invalid XML
        invalid_xml_path = os.path.join(self.temp_dir.name, "invalid.xml")
        with open(invalid_xml_path, "w") as f:
            f.write("<invalid>")
        
        with self.assertRaises(ET.ParseError):
            extract_urls_from_repomix_output(invalid_xml_path)


if __name__ == "__main__":
    unittest.main()
