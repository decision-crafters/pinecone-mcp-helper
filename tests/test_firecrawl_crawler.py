"""
Unit tests for the Firecrawl integration module.
"""

import unittest
from unittest.mock import patch, MagicMock

from repo_ingestion.firecrawl.crawler import (
    extract_urls, init_firecrawl, scrape_url, scrape_urls,
    chunk_firecrawl_content, process_firecrawl_results
)


class TestFirecrawlCrawler(unittest.TestCase):
    """Test cases for the Firecrawl integration module."""

    def test_extract_urls(self):
        """Test extracting URLs from text content."""
        # Test with multiple URLs
        content = """
        This is a test content with multiple URLs:
        https://example.com
        http://test.org/path/to/page
        www.example.org
        https://api.example.com/v1/endpoint?param=value
        """
        
        urls = extract_urls(content)
        
        # Verify URLs
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example.com", urls)
        self.assertIn("http://test.org/path/to/page", urls)
        self.assertIn("https://api.example.com/v1/endpoint?param=value", urls)
        
        # Test with no URLs
        content = "This is a test content with no URLs."
        urls = extract_urls(content)
        self.assertEqual(len(urls), 0)
        
        # Test with duplicate URLs
        content = """
        This is a test content with duplicate URLs:
        https://example.com
        https://example.com
        """
        
        urls = extract_urls(content)
        self.assertEqual(len(urls), 1)
        self.assertIn("https://example.com", urls)

    def test_init_firecrawl(self):
        """Test initializing the Firecrawl client."""
        # Initialize Firecrawl client
        api_key = "test_api_key"
        client = init_firecrawl(api_key)
        
        # Verify client
        self.assertIsNotNone(client)
        self.assertEqual(client["api_key"], api_key)

    @patch('repo_ingestion.firecrawl.crawler.scrape_url')
    def test_scrape_urls(self, mock_scrape_url):
        """Test scraping content from multiple URLs."""
        # Mock scrape_url to return success
        mock_scrape_url.return_value = {
            "content": "Test content",
            "status": "success",
            "url": "https://example.com"
        }
        
        # Scrape URLs
        client = {"api_key": "test_api_key"}
        urls = ["https://example.com", "https://test.org"]
        results = scrape_urls(client, urls)
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["content"], "Test content")
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["url"], "https://example.com")
        
        # Verify scrape_url was called for each URL
        self.assertEqual(mock_scrape_url.call_count, 2)
        
        # Mock scrape_url to raise FirecrawlError for the first URL
        mock_scrape_url.side_effect = [
            Exception("Test error"),
            {
                "content": "Test content",
                "status": "success",
                "url": "https://test.org"
            }
        ]
        
        # Scrape URLs with retry
        results = scrape_urls(client, urls, max_retries=1)
        
        # Verify results (only the second URL should be successful)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Test content")
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["url"], "https://test.org")

    def test_chunk_firecrawl_content(self):
        """Test chunking Firecrawl content."""
        # Test with content shorter than max_chunk_size
        content = "This is a short content."
        chunks = chunk_firecrawl_content(content, max_chunk_size=100)
        
        # Verify chunks
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], content)
        
        # Test with content longer than max_chunk_size
        content = "This is a longer content that needs to be split into multiple chunks. " * 10
        chunks = chunk_firecrawl_content(content, max_chunk_size=100)
        
        # Verify chunks
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)
        
        # Test with overlap
        chunks = chunk_firecrawl_content(content, max_chunk_size=100, overlap=20)
        
        # Verify chunks
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)

    def test_process_firecrawl_results(self):
        """Test processing Firecrawl results."""
        # Test with multiple results
        results = [
            {
                "content": "This is content from the first URL.",
                "url": "https://example.com",
                "status": "success"
            },
            {
                "content": "This is content from the second URL. " * 10,
                "url": "https://test.org",
                "status": "success"
            }
        ]
        
        chunks = process_firecrawl_results(results, max_chunk_size=100)
        
        # Verify chunks
        self.assertGreater(len(chunks), 2)  # Second result should be split into multiple chunks
        
        # Verify first chunk
        self.assertEqual(chunks[0]["text"], "This is content from the first URL.")
        self.assertEqual(chunks[0]["source_type"], "firecrawl")
        self.assertEqual(chunks[0]["source_url"], "https://example.com")
        self.assertEqual(chunks[0]["chunk_index"], 0)
        
        # Verify all chunks have required metadata
        for chunk in chunks:
            self.assertIn("text", chunk)
            self.assertIn("source_type", chunk)
            self.assertIn("source_url", chunk)
            self.assertIn("chunk_index", chunk)
            self.assertEqual(chunk["source_type"], "firecrawl")
        
        # Test with empty results
        chunks = process_firecrawl_results([])
        self.assertEqual(len(chunks), 0)
        
        # Test with results missing content or URL
        results = [
            {
                "content": "This is content.",
                # Missing URL
                "status": "success"
            },
            {
                # Missing content
                "url": "https://test.org",
                "status": "success"
            }
        ]
        
        chunks = process_firecrawl_results(results)
        self.assertEqual(len(chunks), 0)


if __name__ == "__main__":
    unittest.main()
