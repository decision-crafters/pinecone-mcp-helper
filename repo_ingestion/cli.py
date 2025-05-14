"""
Command-line interface for the repository ingestion pipeline.

This module provides the CLI interface for the repository ingestion pipeline,
handling command-line arguments and serving as the entry point for the application.
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from repo_ingestion.config.config_loader import load_config, validate_env_vars
from repo_ingestion.utils.logging_utils import setup_logging
from repo_ingestion.pipeline import run_pipeline, PipelineError

# Configure logger
logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Command-line arguments. If None, sys.argv[1:] is used.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Ingest Git repository content and associated web links into a Pinecone vector database."
    )
    
    parser.add_argument(
        "repo_url",
        help="URL of the Git repository to ingest or path to a local Git repository."
    )
    
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the YAML configuration file. Default: config.yaml"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level. Default: INFO"
    )
    
    parser.add_argument(
        "--no-firecrawl",
        action="store_true",
        help="Disable Firecrawl URL extraction and processing"
    )
    
    parser.add_argument(
        "--no-deep-research",
        action="store_true",
        help="Disable deep research on extracted topics"
    )
    
    parser.add_argument(
        "--search-query",
        help="Specify a search query for Firecrawl and deep research (will override automatic topic extraction)"
    )
    
    parser.add_argument(
        "--mock-mode",
        action="store_true",
        help="Run in mock mode without making actual API calls"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to the log file. If not provided, logs will only be written to the console."
    )
    
    return parser.parse_args(args)


def setup_environment(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Set up the environment for the pipeline.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Dict containing the configuration and environment variables.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required configuration keys or environment variables are missing.
    """
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    
    logger.info("Starting repository ingestion pipeline")
    logger.info(f"Repository URL: {args.repo_url}")
    logger.info(f"Configuration file: {args.config}")
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Validate environment variables
        logger.info("Validating environment variables")
        env_vars = validate_env_vars()
        
        return {
            "config": config,
            "env_vars": env_vars,
            "args": args
        }
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        raise


def main() -> int:
    """
    Main entry point for the repository ingestion pipeline.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        # Parse command-line arguments
        args = parse_args()
        
        # Set up environment
        env = setup_environment(args)
        
        # Run the pipeline
        logger.info("Environment setup complete, starting pipeline")
        results = run_pipeline(args, env["config"], env["env_vars"])
        
        # Log results
        logger.info("Pipeline completed successfully")
        logger.info(f"Repository: {results['repository']}")
        logger.info(f"Index name: {results['index_name']}")
        logger.info(f"Namespace: {results['namespace']}")
        logger.info(f"Repository chunks: {results['repo_chunks']}")
        logger.info(f"Repository vectors upserted: {results['repo_vectors_upserted']}")
        
        # Log Firecrawl results if available
        if 'urls_extracted' in results:
            logger.info(f"URLs extracted: {results['urls_extracted']}")
            logger.info(f"Firecrawl chunks: {results['firecrawl_chunks']}")
            logger.info(f"Firecrawl vectors upserted: {results['firecrawl_vectors_upserted']}")
        else:
            logger.info("Firecrawl processing was disabled")
            
        logger.info(f"Total vectors upserted: {results['total_vectors_upserted']}")
        
        return 0
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error in repository ingestion pipeline: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
