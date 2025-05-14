"""
Search module for the Firecrawl integration.

This module provides functionality to search for web content related to a query
using the Firecrawl API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Find the project root (where the .env file should be)
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"No .env file found at {env_path}")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("dotenv package not found, environment variables may not be loaded")

# Configure logging
logger = logging.getLogger(__name__)


def search_web_content(
    firecrawl_client: Any,
    query: str,
    limit: int = 20,
    scrape_results: bool = True,
    mock_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for web content related to a query using Firecrawl.
    Falls back to a mock implementation if Firecrawl search is not available.

    Args:
        firecrawl_client: Initialized Firecrawl client.
        query: Search query string.
        limit: Maximum number of results to return.
        scrape_results: Whether to scrape the content of search results.

    Returns:
        List of dictionaries containing search results with content.
    """
    try:
        logger.info(f"Searching for web content with query: '{query}'")
        logger.info(f"Firecrawl client type: {type(firecrawl_client)}")
        
        # If in mock mode, skip trying real implementation
        if mock_mode:
            logger.info("Mock mode enabled, skipping real Firecrawl search implementation")
            raise ImportError("Mock mode enabled")
            
        # Check if Firecrawl API key is available
        import os
        firecrawl_api_key = os.environ.get('FIRECRAWL_API_KEY')
        if not firecrawl_api_key:
            logger.warning("FIRECRAWL_API_KEY not found in environment variables")
            logger.info("Falling back to mock implementation due to missing API key")
            raise ImportError("FIRECRAWL_API_KEY not available")
        else:
            logger.info("FIRECRAWL_API_KEY found in environment variables")
            
        # Try to use the Firecrawl client
        try:
            # For the Firecrawl SDK, we don't need to pass scrape options directly to the search function
            # The SDK will handle scraping separately
            logger.info(f"Search parameters: query={query}, limit={limit}")
            
            # Store scrape options for later use if needed
            scrape_options = {
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 1000  # Wait 1 second for dynamic content
            } if scrape_results else None
            
            # Check if firecrawl_client is a FirecrawlClient instance
            from repo_ingestion.firecrawl.crawler import FirecrawlClient
            
            if isinstance(firecrawl_client, FirecrawlClient):
                logger.info("Using FirecrawlClient instance search method")
                search_results = firecrawl_client.search(
                    query=query,
                    limit=limit,
                    scrapeOptions=scrape_options
                )
            # Check if firecrawl_client has a search method (duck typing)
            elif hasattr(firecrawl_client, 'search') and callable(getattr(firecrawl_client, 'search')):
                logger.info("Using firecrawl_client.search method")
                search_results = firecrawl_client.search(
                    query=query,
                    limit=limit,
                    scrapeOptions=scrape_options
                )
            # Try to use the MCP function directly
            elif 'mcp1_firecrawl_search' in globals():
                logger.info("Using mcp1_firecrawl_search function directly")
                search_results = mcp1_firecrawl_search(
                    query=query,
                    limit=limit,
                    scrapeOptions=scrape_options
                )
            else:
                # Try to use the MCP server function directly
                logger.info("Attempting to access mcp1_firecrawl_search from main module")
                import sys
                
                if 'mcp1_firecrawl_search' in dir(sys.modules['__main__']):
                    logger.info("Found mcp1_firecrawl_search in main module")
                    search_func = getattr(sys.modules['__main__'], 'mcp1_firecrawl_search')
                    
                    # Prepare parameters
                    params = {
                        'query': query,
                        'limit': limit
                    }
                    
                    if scrape_options:
                        params['scrapeOptions'] = scrape_options
                    
                    # Perform the search
                    logger.info("Executing Firecrawl search via MCP server...")
                    search_results = search_func(**params)
                else:
                    logger.warning("mcp1_firecrawl_search not found in main module")
                    raise ImportError("mcp1_firecrawl_search not available")
            
            logger.info("Firecrawl search completed")
            
            # Process search results
            results = []
            
            if "results" in search_results:
                for result in search_results["results"]:
                    # Extract URL and title
                    url = result.get("url", "")
                    title = result.get("title", "")
                    
                    # Extract content if available
                    content = ""
                    if "content" in result and "markdown" in result["content"]:
                        content = result["content"]["markdown"]
                    
                    # Create result object
                    result_obj = {
                        "url": url,
                        "title": title,
                        "content": content,
                        "source_type": "web_search",
                        "metadata": {
                            "api_used": "firecrawl",
                            "query": query
                        }
                    }
                    
                    results.append(result_obj)
                    
                logger.info(f"Found {len(results)} search results for query: '{query}'")
                return results
            else:
                logger.warning(f"No search results found for query: '{query}'")
                return []
                
        except ImportError as ie:
            logger.warning(f"Firecrawl search MCP function not available: {ie}")
            logger.info("Falling back to mock implementation")
            # Fall through to mock implementation
        except Exception as e:
            logger.warning(f"Error during Firecrawl search: {e}")
            logger.info("Falling back to mock implementation")
            # Fall through to mock implementation
        
        # Mock implementation when Firecrawl search is not available or mock mode is enabled
        if mock_mode:
            logger.info("Using mock implementation due to mock mode being enabled")
        else:
            logger.info("Using mock implementation because Firecrawl search is not available")
            
        # Log the specific reason for falling back to mock implementation
        import os
        if not os.environ.get('FIRECRAWL_API_KEY'):
            logger.warning("Reason: FIRECRAWL_API_KEY not found in environment variables")
        
        # Check if MCP functions are available
        import sys
        if 'mcp1_firecrawl_search' not in dir(sys.modules['__main__']):
            logger.warning("Reason: mcp1_firecrawl_search function not available in main module")
        else:
            logger.warning("Reason: Other error occurred during Firecrawl search")
        
        # Create more realistic mock search results based on the query
        mock_results = [
            {
                "url": f"https://example.com/documentation/{query.replace(' ', '-')}",
                "title": f"Comprehensive Guide to {query.title()}",
                "content": f"# {query.title()} Documentation\n\nThis is comprehensive documentation about {query}. The search query was used to generate this result for testing purposes.\n\n## Key Features\n\n- Feature 1: Description of feature 1 related to {query}\n- Feature 2: Description of feature 2 related to {query}\n- Feature 3: Description of feature 3 related to {query}\n\n## Usage Examples\n\n```python\n# Example code for {query}\nimport {query.lower().replace(' ', '_')}\n\nresult = {query.lower().replace(' ', '_')}.process()\nprint(result)\n```",
                "source_type": "web_search_mock"
            },
            {
                "url": f"https://example.com/tutorials/{query.replace(' ', '-')}-guide",
                "title": f"Advanced Tutorial: Working with {query.title()}",
                "content": f"# Advanced {query.title()} Tutorial\n\nThis tutorial covers advanced techniques for working with {query}.\n\n## Prerequisites\n\n- Basic understanding of {query}\n- Familiarity with related technologies\n\n## Advanced Topics\n\n1. Integration with other systems\n2. Performance optimization\n3. Security considerations\n\n## Best Practices\n\nWhen working with {query}, consider the following best practices:\n\n- Always validate inputs\n- Use proper error handling\n- Follow the principle of least privilege",
                "source_type": "web_search_mock"
            },
            {
                "url": f"https://example.com/blog/latest-developments-in-{query.replace(' ', '-')}",
                "title": f"Latest Developments in {query.title()} Technology",
                "content": f"# Latest Developments in {query.title()}\n\nStay up-to-date with the most recent advancements in {query} technology.\n\n## Recent Updates\n\n- New version released with improved performance\n- Enhanced security features\n- Better integration capabilities\n\n## Community Contributions\n\nThe {query} community has been actively contributing to its development:\n\n- New plugins and extensions\n- Comprehensive documentation\n- Active support forums",
                "source_type": "web_search_mock"
            }
        ]
        
        logger.info(f"Created {len(mock_results)} mock search results for query: '{query}'")
        return mock_results
    
    except Exception as e:
        logger.error(f"Error searching for web content: {e}")
        return []
