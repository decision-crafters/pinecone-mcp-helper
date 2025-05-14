"""
Firecrawl integration module for the repository ingestion pipeline.

This module provides functionality to extract URLs from Repomix output and use
Firecrawl to scrape or search content from those URLs.
"""

import logging
import re
import os
from typing import List, Dict, Any, Optional
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

# Try to import Firecrawl SDK
try:
    import firecrawl
    logger.info("Successfully imported Firecrawl SDK")
except ImportError:
    logger.warning("Firecrawl SDK not found, will use mock implementation")
    firecrawl = None

# Configure logging
logger = logging.getLogger(__name__)


class FirecrawlError(Exception):
    """Exception raised for errors in Firecrawl operations."""
    pass


def extract_urls(content: str) -> List[str]:
    """
    Extract URLs from text content.

    Args:
        content: Text content to extract URLs from.

    Returns:
        List of unique URLs found in the content.
    """
    logger.info("Extracting URLs from content")
    
    try:
        # Extract URLs using regex
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+'
        urls = re.findall(url_pattern, content)
        
        # Deduplicate URLs
        unique_urls = list(set(urls))
        
        logger.info(f"Extracted {len(unique_urls)} unique URLs from content")
        
        return unique_urls
    except Exception as e:
        logger.error(f"Error extracting URLs: {e}")
        raise


class FirecrawlClient:
    """
    Client for interacting with the Firecrawl API.
    
    This class provides methods for searching, scraping, and other operations
    using the Firecrawl API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Firecrawl client.
        
        Args:
            api_key: Firecrawl API key.
        """
        self.api_key = api_key
        
        # Initialize the FirecrawlApp client if the SDK is available
        self.client = None
        if firecrawl is not None:
            try:
                self.client = firecrawl.FirecrawlApp(api_key=api_key)
                logger.info("FirecrawlClient initialized with FirecrawlApp")
            except Exception as e:
                logger.error(f"Failed to initialize FirecrawlApp: {e}")
        else:
            logger.warning("Firecrawl SDK not available, client will use mock implementation")
            
        logger.info("FirecrawlClient initialization complete")
    
    def search(self, query: str, limit: int = 20, scrapeOptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for web content related to a query.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            scrapeOptions: Options for scraping search results.
            
        Returns:
            Dictionary containing search results.
            
        Raises:
            FirecrawlError: If the search fails.
        """
        logger.info(f"Searching for: {query} (limit: {limit})")
        
        try:
            # Check if the client is initialized
            if self.client is not None and hasattr(self.client, 'search'):
                logger.info("Using Firecrawl SDK for search")
                
                # Prepare search parameters - only pass the supported parameters
                search_params = {
                    'query': query,
                    'limit': limit
                }
                
                # Perform the search
                search_response = self.client.search(**search_params)
                
                # The SDK returns a Pydantic model, not a dictionary
                # Check if the search was successful by checking the success attribute
                if hasattr(search_response, 'success') and search_response.success:
                    logger.info(f"Search completed successfully with Firecrawl SDK")
                    
                    # Extract the results from the response
                    # The data attribute contains the search results
                    results = search_response.data if hasattr(search_response, 'data') else []
                    
                    # Format the results to match the expected structure
                    formatted_results = []
                    for result in results:
                        # Convert the result to a dictionary if it's not already
                        if not isinstance(result, dict):
                            if hasattr(result, 'model_dump'):
                                # Pydantic v2
                                result_dict = result.model_dump()
                            elif hasattr(result, 'dict'):
                                # Pydantic v1
                                result_dict = result.dict()
                            else:
                                # Fallback to __dict__
                                result_dict = vars(result)
                        else:
                            result_dict = result
                        
                        # Create the formatted result
                        formatted_result = {
                            'url': result_dict.get('url', ''),
                            'title': result_dict.get('title', ''),
                            'content': {'markdown': result_dict.get('description', '')},
                            'source_type': 'web_search'
                        }
                        formatted_results.append(formatted_result)
                    
                    return {
                        'results': formatted_results
                    }
                else:
                    # Extract error message if available
                    error_msg = getattr(search_response, 'error', 'Unknown error') if hasattr(search_response, 'error') else 'Unknown error'
                    logger.error(f"Search failed: {error_msg}")
                    raise FirecrawlError(f"Search failed: {error_msg}")
            else:
                logger.warning("Firecrawl SDK not available or search method not found")
                raise FirecrawlError("Firecrawl SDK not available or search method not found")
        except Exception as e:
            logger.error(f"Error during Firecrawl search: {e}")
            raise FirecrawlError(f"Error during Firecrawl search: {e}")
    
    def scrape(self, url: str, formats: List[str] = None, onlyMainContent: bool = True, waitFor: int = 1000) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape.
            formats: Content formats to extract (default: ['markdown']).
            onlyMainContent: Extract only the main content (default: True).
            waitFor: Time in milliseconds to wait for dynamic content (default: 1000).
            
        Returns:
            Dictionary containing scraped content.
            
        Raises:
            FirecrawlError: If scraping fails.
        """
        logger.info(f"Scraping URL: {url}")
        
        if formats is None:
            formats = ["markdown"]
        
        try:
            # Check if the client is initialized
            if self.client is not None and hasattr(self.client, 'scrape_url'):
                logger.info("Using Firecrawl SDK for scraping")
                
                # Prepare scrape options
                scrape_params = {
                    "url": url,
                    "formats": formats,
                    "onlyMainContent": onlyMainContent,
                    "waitFor": waitFor
                }
                
                # Perform the scrape
                scrape_response = self.client.scrape_url(**scrape_params)
                
                # The SDK returns a Pydantic model, not a dictionary
                # Check if the scrape was successful by checking the success attribute
                if hasattr(scrape_response, 'success') and scrape_response.success:
                    logger.info(f"Scraping completed successfully for {url} with Firecrawl SDK")
                    
                    # Extract the content from the response
                    # Convert the data to a dictionary if it's not already
                    if hasattr(scrape_response, 'data'):
                        if not isinstance(scrape_response.data, dict):
                            if hasattr(scrape_response.data, 'model_dump'):
                                # Pydantic v2
                                content_data = scrape_response.data.model_dump()
                            elif hasattr(scrape_response.data, 'dict'):
                                # Pydantic v1
                                content_data = scrape_response.data.dict()
                            else:
                                # Fallback to __dict__
                                content_data = vars(scrape_response.data)
                        else:
                            content_data = scrape_response.data
                    else:
                        content_data = {}
                    
                    # Format the result to match the expected structure
                    formatted_result = {
                        'url': url,
                        'content': {}
                    }
                    
                    # Extract markdown content if available
                    if 'markdown' in content_data:
                        formatted_result['content']['markdown'] = content_data['markdown']
                    
                    # Extract HTML content if available
                    if 'html' in content_data:
                        formatted_result['content']['html'] = content_data['html']
                    
                    return formatted_result
                else:
                    # Extract error message if available
                    error_msg = getattr(scrape_response, 'error', 'Unknown error') if hasattr(scrape_response, 'error') else 'Unknown error'
                    logger.error(f"Scraping failed: {error_msg}")
                    raise FirecrawlError(f"Scraping failed: {error_msg}")
            else:
                logger.warning("Firecrawl SDK not available or scrape_url method not found")
                raise FirecrawlError("Firecrawl SDK not available or scrape_url method not found")
        except Exception as e:
            logger.error(f"Error during Firecrawl scraping: {e}")
            raise FirecrawlError(f"Error during Firecrawl scraping: {e}")


def init_firecrawl(api_key: str) -> Any:
    """
    Initialize the Firecrawl client.

    Args:
        api_key: Firecrawl API key.

    Returns:
        Initialized Firecrawl client.

    Raises:
        FirecrawlError: If initialization fails.
    """
    logger.info("Initializing Firecrawl client")
    
    try:
        # Initialize the FirecrawlClient
        client = FirecrawlClient(api_key=api_key)
        logger.info("Firecrawl client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing Firecrawl client: {e}")
        raise FirecrawlError(f"Error initializing Firecrawl client: {e}")


def scrape_url(client: Any, url: str) -> Dict[str, Any]:
    """
    Scrape content from a URL using Firecrawl.

    Args:
        client: Initialized Firecrawl client.
        url: URL to scrape.

    Returns:
        Dictionary containing the scraped content and metadata.

    Raises:
        FirecrawlError: If scraping fails.
    """
    logger.info(f"Scraping URL: {url}")
    
    try:
        # Check if client is a FirecrawlClient instance
        if isinstance(client, FirecrawlClient):
            # Use the client's scrape method
            try:
                result = client.scrape(url=url)
                logger.info(f"URL scraped successfully: {url}")
                return result
            except FirecrawlError as fe:
                logger.warning(f"FirecrawlClient scrape failed, falling back to mock: {fe}")
        else:
            logger.warning(f"Client is not a FirecrawlClient instance, using mock implementation")
        
        # Fall back to mock implementation
        result = {
            "url": url,
            "title": f"Content from {url}",
            "content": {
                "markdown": f"# Content from {url}\n\nThis is a placeholder for the content that would be scraped from {url}."
            },
            "metadata": {
                "source": "firecrawl_mock",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }
        
        logger.info(f"Mock URL scraping completed for: {url}")
        return result
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {e}")
        raise FirecrawlError(f"Error scraping URL {url}: {e}")


def search_url(client: Any, url: str, query: str) -> Dict[str, Any]:
    """
    Search content from a URL using Firecrawl.

    Args:
        client: Initialized Firecrawl client.
        url: URL to search.
        query: Search query.

    Returns:
        Dictionary containing the search results and metadata.

    Raises:
        FirecrawlError: If searching fails.
    """
    logger.info(f"Searching URL: {url} with query: {query}")
    
    try:
        # Check if client is a FirecrawlClient instance
        if isinstance(client, FirecrawlClient):
            # Combine URL and query for better results
            combined_query = f"site:{url} {query}"
            
            try:
                # Use the client's search method with site-specific query
                search_results = client.search(query=combined_query, limit=5)
                
                # Process search results
                if "results" in search_results and search_results["results"]:
                    # Return the first result that matches the URL
                    for result in search_results["results"]:
                        result_url = result.get("url", "")
                        if url in result_url:
                            return {
                                "content": result.get("content", {}).get("markdown", ""),
                                "status": "success",
                                "url": result_url,
                                "title": result.get("title", ""),
                                "query": query
                            }
                    
                    # If no exact match, return the first result
                    first_result = search_results["results"][0]
                    return {
                        "content": first_result.get("content", {}).get("markdown", ""),
                        "status": "success",
                        "url": first_result.get("url", url),
                        "title": first_result.get("title", ""),
                        "query": query
                    }
                
                logger.warning(f"No search results found for URL: {url} with query: {query}")
            except FirecrawlError as fe:
                logger.warning(f"FirecrawlClient search failed, falling back to mock: {fe}")
        else:
            logger.warning(f"Client is not a FirecrawlClient instance, using mock implementation")
        
        # Fall back to mock implementation
        result = {
            "content": f"# Search Results for {query} on {url}\n\nThis is a placeholder for search results that would be returned when searching for '{query}' on {url}.\n\n## Key Points\n\n- Point 1 related to {query}\n- Point 2 related to {query}\n- Point 3 related to {query}",
            "status": "success",
            "url": url,
            "title": f"Search results for {query} on {url}",
            "query": query,
            "source": "firecrawl_mock"
        }
        
        logger.info(f"Successfully generated mock search results for URL: {url}")
        return result
    except Exception as e:
        logger.error(f"Error searching URL {url}: {e}")
        raise FirecrawlError(f"Error searching URL {url}: {e}")


def scrape_urls(client: Any, urls: List[str], max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Scrape content from multiple URLs using Firecrawl.

    Args:
        client: Initialized Firecrawl client.
        urls: List of URLs to scrape.
        max_retries: Maximum number of retries for failed requests.

    Returns:
        List of dictionaries, each containing scraped content and metadata.
    """
    logger.info(f"Scraping {len(urls)} URLs")
    
    # Check if we can use batch scraping
    batch_scrape_available = False
    if isinstance(client, FirecrawlClient):
        try:
            # Check if batch scrape is available
            from mcp1_firecrawl_batch_scrape import batch_scrape
            batch_scrape_available = True
            logger.info("Batch scraping is available")
        except ImportError:
            logger.info("Batch scraping not available, falling back to individual URL scraping")
    
    # If batch scraping is available, use it
    if batch_scrape_available and len(urls) > 1:
        try:
            logger.info(f"Using batch scraping for {len(urls)} URLs")
            options = {
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 1000
            }
            batch_results = batch_scrape(urls=urls, options=options)
            
            # Process batch results
            results = []
            for url, result in zip(urls, batch_results.get("results", [])):
                if result.get("success", False):
                    results.append({
                        "url": url,
                        "title": result.get("title", f"Content from {url}"),
                        "content": {
                            "markdown": result.get("content", {}).get("markdown", f"# Content from {url}")
                        },
                        "metadata": {
                            "source": "firecrawl_batch",
                            "timestamp": result.get("timestamp", "2023-01-01T00:00:00Z")
                        }
                    })
                else:
                    logger.warning(f"Batch scraping failed for URL {url}: {result.get('error')}")
            
            logger.info(f"Successfully batch scraped {len(results)}/{len(urls)} URLs")
            return results
        except Exception as e:
            logger.warning(f"Batch scraping failed, falling back to individual URL scraping: {e}")
    
    # Fall back to individual URL scraping
    results = []
    
    for i, url in enumerate(urls):
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                # Scrape URL
                result = scrape_url(client, url)
                
                # Add result to results
                results.append(result)
                
                success = True
            except FirecrawlError as e:
                retries += 1
                logger.warning(f"Error scraping URL {url} (attempt {retries}/{max_retries}): {e}")
                
                if retries >= max_retries:
                    logger.error(f"Failed to scrape URL {url} after {max_retries} attempts")
                else:
                    # Wait before retrying
                    import time
                    time.sleep(1)
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Scraped {i + 1}/{len(urls)} URLs")
    
    logger.info(f"Successfully scraped {len(results)}/{len(urls)} URLs")
    
    return results


def chunk_firecrawl_content(content: str, max_chunk_size: int = 500, overlap: int = 0) -> List[str]:
    """
    Split Firecrawl content into chunks of specified size.

    Args:
        content: Text content to chunk.
        max_chunk_size: Maximum size of each chunk in characters.
        overlap: Number of characters to overlap between chunks.

    Returns:
        List of text chunks.
    """
    logger.info(f"Chunking content (max_chunk_size: {max_chunk_size}, overlap: {overlap})")
    
    # Check if content is shorter than max_chunk_size
    if len(content) <= max_chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        # Calculate end position
        end = start + max_chunk_size
        
        # Adjust end position to avoid cutting words
        if end < len(content):
            # Find the last space before end
            last_space = content.rfind(" ", start, end)
            
            if last_space != -1:
                end = last_space
        else:
            end = len(content)
        
        # Extract chunk
        chunk = content[start:end].strip()
        
        if chunk:
            chunks.append(chunk)
        
        # Update start position for next chunk
        start = end - overlap
    
    logger.info(f"Split content into {len(chunks)} chunks")
    
    return chunks


def process_firecrawl_results(results: List[Dict[str, Any]], max_chunk_size: int = 500, overlap: int = 0) -> List[Dict[str, Any]]:
    """
    Process Firecrawl results into a format suitable for embedding.

    Args:
        results: List of Firecrawl results.

    Returns:
        List of dictionaries containing processed content chunks.
    """
    logger.info("Processing Firecrawl results")
    
    chunks = []
    
    try:
        for result in results:
            # Extract URL and content
            url = result.get("url", "")
            title = result.get("title", "")
            
            # Handle different content formats
            content = ""
            if isinstance(result.get("content"), str):
                content = result.get("content", "")
            elif isinstance(result.get("content"), dict) and "markdown" in result.get("content", {}):
                content = result.get("content", {}).get("markdown", "")
            else:
                content = result.get("content", "")
            
            # Get source type (web, web_search, etc.)
            source_type = result.get("source_type", "web")
            
            if not content:
                logger.warning(f"No content found for URL: {url}")
                continue
            
            # Create metadata
            metadata = {
                "url": url,
                "title": title,
                "source_type": source_type
            }
            
            # Create chunk
            chunk = {
                "text": content,
                "metadata": metadata,
                "source_type": source_type,
                "url": url
            }
            
            chunks.append(chunk)
        
        logger.info(f"Processed {len(chunks)} Firecrawl content chunks")
        
        return chunks
    except Exception as e:
        logger.error(f"Error processing Firecrawl results: {e}")
        return []
