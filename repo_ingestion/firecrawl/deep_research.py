"""
Firecrawl deep research integration for the repository ingestion pipeline.

This module provides functionality to enhance repository content with additional context
using Firecrawl's deep research capabilities.
"""

import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


class FirecrawlResearchError(Exception):
    """Exception raised for errors in Firecrawl research operations."""
    pass


async def perform_deep_research(topics: List[str], max_depth: int = 3, max_urls: int = 10) -> Dict[str, Any]:
    """
    Perform deep research on a list of topics using Firecrawl.

    Args:
        topics: List of topics to research.
        max_depth: Maximum depth of research iterations (1-10).
        max_urls: Maximum number of URLs to analyze (1-1000).

    Returns:
        Dictionary containing research results.

    Raises:
        FirecrawlResearchError: If research fails.
    """
    from mcp1_firecrawl_deep_research import deep_research
    
    logger.info(f"Performing deep research on {len(topics)} topics")
    
    results = {}
    
    for topic in topics:
        logger.info(f"Researching topic: {topic}")
        
        try:
            # Call Firecrawl deep research
            research_result = deep_research(
                query=topic,
                maxDepth=max_depth,
                maxUrls=max_urls,
                timeLimit=180  # 3 minutes per topic
            )
            
            results[topic] = research_result
            logger.info(f"Research completed for topic: {topic}")
            
        except Exception as e:
            logger.warning(f"Error researching topic '{topic}': {e}")
            results[topic] = {"error": str(e)}
    
    return results


def extract_research_topics(content_chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Extract research topics from content chunks.

    Args:
        content_chunks: List of content chunks from repository.

    Returns:
        List of topics for deep research.
    """
    topics = []
    
    for chunk in content_chunks:
        # Extract potential topics from content
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})
        
        # Add repository name as a topic
        repo_name = metadata.get("repository_name")
        if repo_name and repo_name not in topics:
            topics.append(repo_name)
        
        # Add main technologies as topics
        tech_stack = metadata.get("tech_stack", [])
        for tech in tech_stack:
            if tech and tech not in topics:
                topics.append(tech)
    
    # Limit to 5 topics to avoid excessive API calls
    return topics[:5]


def enrich_content_with_research(content_chunks: List[Dict[str, Any]], research_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Enrich content chunks with research results.

    Args:
        content_chunks: List of content chunks from repository.
        research_results: Dictionary of research results by topic.

    Returns:
        Enriched content chunks.
    """
    enriched_chunks = []
    
    for chunk in content_chunks:
        # Create a copy of the chunk
        enriched_chunk = chunk.copy()
        
        # Add research context to metadata
        metadata = enriched_chunk.get("metadata", {})
        metadata["research_context"] = {}
        
        # Find relevant research for this chunk
        for topic, result in research_results.items():
            if "error" not in result:
                metadata["research_context"][topic] = result
        
        enriched_chunk["metadata"] = metadata
        enriched_chunks.append(enriched_chunk)
    
    return enriched_chunks
