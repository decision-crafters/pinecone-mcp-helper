"""
Unit tests for the configuration loader module.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import yaml

from repo_ingestion.config.config_loader import (
    load_config, validate_env_vars, get_nested_config
)


class TestConfigLoader(unittest.TestCase):
    """Test cases for the configuration loader module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.yaml")
        
        # Sample config data
        self.config_data = {
            "pinecone": {
                "dimension": 1536,
                "metric": "cosine"
            },
            "embedding": {
                "model": "multilingual-e5-large"
            }
        }
        
        # Write config data to file
        with open(self.config_path, "w") as f:
            yaml.dump(self.config_data, f)

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_load_config(self):
        """Test loading configuration from a YAML file."""
        config = load_config(self.config_path)
        
        self.assertEqual(config["pinecone"]["dimension"], 1536)
        self.assertEqual(config["pinecone"]["metric"], "cosine")
        self.assertEqual(config["embedding"]["model"], "multilingual-e5-large")

    def test_load_config_file_not_found(self):
        """Test loading configuration from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_config("/path/to/nonexistent/config.yaml")

    def test_load_config_missing_keys(self):
        """Test loading configuration with missing required keys."""
        # Create config with missing keys
        config_data = {
            "pinecone": {
                "dimension": 1536
                # Missing "metric" key
            },
            "embedding": {
                "model": "multilingual-e5-large"
            }
        }
        
        # Write config data to file
        config_path = os.path.join(self.temp_dir.name, "invalid_config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        with self.assertRaises(ValueError):
            load_config(config_path)

    @patch.dict(os.environ, {
        "PINECONE_API_KEY": "test_api_key",
        "PINECONE_ENVIRONMENT": "test_environment",
        "FIRECRAWL_API_KEY": "test_firecrawl_key"
    })
    def test_validate_env_vars(self):
        """Test validating environment variables."""
        env_vars = validate_env_vars()
        
        self.assertEqual(env_vars["PINECONE_API_KEY"], "test_api_key")
        self.assertEqual(env_vars["PINECONE_ENVIRONMENT"], "test_environment")
        self.assertEqual(env_vars["FIRECRAWL_API_KEY"], "test_firecrawl_key")

    @patch.dict(os.environ, {
        "PINECONE_API_KEY": "test_api_key",
        # Missing PINECONE_ENVIRONMENT
        "FIRECRAWL_API_KEY": "test_firecrawl_key"
    })
    def test_validate_env_vars_missing(self):
        """Test validating environment variables with missing required variables."""
        with self.assertRaises(ValueError):
            validate_env_vars()

    def test_get_nested_config(self):
        """Test getting nested configuration values using dot notation."""
        config = {
            "pinecone": {
                "dimension": 1536,
                "metric": "cosine"
            },
            "embedding": {
                "model": "multilingual-e5-large"
            }
        }
        
        self.assertEqual(get_nested_config(config, "pinecone.dimension"), 1536)
        self.assertEqual(get_nested_config(config, "pinecone.metric"), "cosine")
        self.assertEqual(get_nested_config(config, "embedding.model"), "multilingual-e5-large")
        
        # Test with default value
        self.assertIsNone(get_nested_config(config, "nonexistent.key"))
        self.assertEqual(get_nested_config(config, "nonexistent.key", "default"), "default")


if __name__ == "__main__":
    unittest.main()
