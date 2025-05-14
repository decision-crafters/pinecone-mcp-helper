#!/usr/bin/env python
"""
Debug script to test the Firecrawl integration with detailed logging.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
project_root = Path(__file__).parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.error(f"No .env file found at {env_path}")
    sys.exit(1)

# Check if the API key is loaded
firecrawl_api_key = os.environ.get('FIRECRAWL_API_KEY')
if firecrawl_api_key:
    logger.info(f"FIRECRAWL_API_KEY found: {firecrawl_api_key[:5]}...{firecrawl_api_key[-5:]}")
else:
    logger.error("FIRECRAWL_API_KEY not found in environment variables")
    sys.exit(1)

# Import our FirecrawlClient implementation
try:
    from repo_ingestion.firecrawl.crawler import FirecrawlClient, FirecrawlError
    logger.info("Successfully imported FirecrawlClient")
except ImportError as e:
    logger.error(f"Failed to import FirecrawlClient: {e}")
    sys.exit(1)

# Import the search function
try:
    from repo_ingestion.firecrawl.search import search_web_content
    logger.info("Successfully imported search_web_content")
except ImportError as e:
    logger.error(f"Failed to import search_web_content: {e}")
    sys.exit(1)

# Try to create a FirecrawlClient
try:
    client = FirecrawlClient(api_key=firecrawl_api_key)
    logger.info("Successfully created FirecrawlClient")
    
    # Check if the client has a Firecrawl SDK client
    if hasattr(client, 'client') and client.client is not None:
        logger.info("FirecrawlClient has a valid SDK client")
    else:
        logger.warning("FirecrawlClient does not have a valid SDK client")
except Exception as e:
    logger.error(f"Failed to create FirecrawlClient: {e}")
    sys.exit(1)

# Try to perform a search using the client directly
try:
    logger.info("\nTesting search directly with FirecrawlClient...")
    search_results = client.search(query="configuration management best practices", limit=3)
    logger.info(f"Search successful! Results: {search_results}")
    
    # Check if the results have the expected structure
    if 'results' in search_results:
        results = search_results['results']
        logger.info(f"Found {len(results)} results")
        
        # Print the first result
        if results:
            first_result = results[0]
            logger.info(f"\nFirst result:")
            logger.info(f"URL: {first_result.get('url', 'N/A')}")
            logger.info(f"Title: {first_result.get('title', 'N/A')}")
            logger.info(f"Source Type: {first_result.get('source_type', 'N/A')}")
            
            # Check if content is available
            if 'content' in first_result and 'markdown' in first_result['content']:
                content_preview = first_result['content']['markdown'][:100] + "..."
                logger.info(f"Content preview: {content_preview}")
    else:
        logger.warning("Search results do not have the expected structure")
except Exception as e:
    logger.error(f"Direct search failed: {e}")
    import traceback
    traceback.print_exc()

# Try to perform a search using the search_web_content function
try:
    logger.info("\nTesting search_web_content function...")
    # Test with mock_mode=False to force using the real implementation
    search_results = search_web_content(client, "configuration management best practices", limit=3, mock_mode=False)
    logger.info(f"search_web_content successful! Found {len(search_results)} results")
    
    # Print the first result
    if search_results:
        first_result = search_results[0]
        logger.info(f"\nFirst result:")
        logger.info(f"URL: {first_result.get('url', 'N/A')}")
        logger.info(f"Title: {first_result.get('title', 'N/A')}")
        logger.info(f"Source Type: {first_result.get('source_type', 'N/A')}")
        
        # Check if content is available
        if 'content' in first_result and isinstance(first_result['content'], dict) and 'markdown' in first_result['content']:
            content_preview = first_result['content']['markdown'][:100] + "..."
            logger.info(f"Content preview: {content_preview}")
except Exception as e:
    logger.error(f"search_web_content failed: {e}")
    import traceback
    traceback.print_exc()

# Try to perform a search using the search_web_content function with mock_mode=True
try:
    logger.info("\nTesting search_web_content function with mock_mode=True...")
    search_results = search_web_content(client, "configuration management best practices", limit=3, mock_mode=True)
    logger.info(f"search_web_content (mock) successful! Found {len(search_results)} results")
    
    # Print the first result
    if search_results:
        first_result = search_results[0]
        logger.info(f"\nFirst result:")
        logger.info(f"URL: {first_result.get('url', 'N/A')}")
        logger.info(f"Title: {first_result.get('title', 'N/A')}")
        logger.info(f"Source Type: {first_result.get('source_type', 'N/A')}")
except Exception as e:
    logger.error(f"search_web_content (mock) failed: {e}")
    import traceback
    traceback.print_exc()

logger.info("\nDebugging completed!")
