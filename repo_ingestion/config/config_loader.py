"""
Configuration loader module for the repository ingestion pipeline.

This module handles loading configuration from YAML files and validating
environment variables required for the pipeline.
"""

import os
import logging
from typing import Dict, Any, Optional

import yaml
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = [
    "PINECONE_API_KEY",
    "PINECONE_ENVIRONMENT",
    "FIRECRAWL_API_KEY",
]

# Optional environment variables (required based on configuration)
OPTIONAL_ENV_VARS = [
    "EMBEDDING_API_KEY",
]

# Required configuration keys
REQUIRED_CONFIG_KEYS = [
    "pinecone.dimension",
    "pinecone.metric",
    "embedding.model",
]


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dict containing the configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the configuration file is not valid YAML.
        ValueError: If required configuration keys are missing.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required configuration keys
        _validate_config(config)
        
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that the configuration contains all required keys.

    Args:
        config: Configuration dictionary.

    Raises:
        ValueError: If required configuration keys are missing.
    """
    missing_keys = []
    
    for key_path in REQUIRED_CONFIG_KEYS:
        parts = key_path.split('.')
        current = config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                missing_keys.append(key_path)
                break
            current = current[part]
    
    if missing_keys:
        error_msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def validate_env_vars() -> Dict[str, str]:
    """
    Validate that all required environment variables are set.

    Returns:
        Dict containing the environment variables.

    Raises:
        ValueError: If required environment variables are missing.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    env_vars = {}
    missing_vars = []
    
    # Check required environment variables
    for var in REQUIRED_ENV_VARS:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    # Check optional environment variables
    for var in OPTIONAL_ENV_VARS:
        value = os.environ.get(var)
        if value:
            env_vars[var] = value
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return env_vars


def get_nested_config(config: Dict[str, Any], key_path: str, default: Optional[Any] = None) -> Any:
    """
    Get a nested configuration value using dot notation.

    Args:
        config: Configuration dictionary.
        key_path: Dot-separated path to the configuration value.
        default: Default value to return if the key is not found.

    Returns:
        The configuration value or the default value if not found.
    """
    parts = key_path.split('.')
    current = config
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    
    return current
