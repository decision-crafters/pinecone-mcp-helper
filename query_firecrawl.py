#!/usr/bin/env python
"""
Script to query Pinecone index for Firecrawl content.
"""

# Set protobuf environment variable to fix compatibility issue
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
project_root = Path(__file__).parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"No .env file found at {env_path}")

# Import necessary modules
try:
    from repo_ingestion.pinecone.index_manager import init_pinecone, get_namespace_for_repo
    from repo_ingestion.embedding.embedder import get_embedding_function
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def query_firecrawl_content(
    query: str,
    repo_name: str,
    top_k: int = 10,
    filter_source_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query the Pinecone index for Firecrawl content.
    
    Args:
        query: The query string.
        repo_name: The repository name.
        top_k: Maximum number of results to return.
        filter_source_type: Optional filter for source_type (e.g., 'web_search', 'web_search_mock').
        
    Returns:
        List of query results.
    """
    # Set environment variable for protobuf
    os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=os.environ.get("PINECONE_API_KEY"),
        environment=os.environ.get("PINECONE_ENVIRONMENT")
    )
    
    # Get the index name and namespace
    index_name = f"{repo_name}-repo"
    namespace = get_namespace_for_repo(repo_name)
    
    logger.info(f"Querying index '{index_name}' in namespace '{namespace}' for: {query}")
    
    # Get the index
    index = pinecone_client.Index(index_name)
    
    # Initialize the embedding function
    embedding_function = get_embedding_function(
        config={"embedding": {"model": "pinecone-sparse-english-v0"}},
        env_vars={"EMBEDDING_API_KEY": os.environ.get("EMBEDDING_API_KEY")}
    )
    
    # Embed the query
    query_embedding = embedding_function(query)
    
    # Create the filter
    filter_dict = {}
    if filter_source_type:
        filter_dict["source_type"] = {"$eq": filter_source_type}
    
    # Execute the query
    try:
        query_response = index.query(
            namespace=namespace,
            top_k=top_k,
            include_metadata=True,
            vector=query_embedding,
            filter=filter_dict if filter_dict else None
        )
        
        # Process the results
        results = []
        matches = query_response.matches if hasattr(query_response, 'matches') else []
        
        for match in matches:
            result = {
                "id": match.id if hasattr(match, 'id') else None,
                "score": match.score if hasattr(match, 'score') else None,
                "text": match.metadata.get("text", "") if hasattr(match, 'metadata') else "",
                "source_type": match.metadata.get("source_type", "unknown") if hasattr(match, 'metadata') else "unknown",
                "url": match.metadata.get("url", "") if hasattr(match, 'metadata') else "",
                "title": match.metadata.get("title", "") if hasattr(match, 'metadata') else "",
            }
            results.append(result)
        
        return results
    except Exception as e:
        logger.error(f"Error querying Pinecone: {e}")
        return []

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query Pinecone index for Firecrawl content.")
    parser.add_argument("--repo", required=True, help="Repository name.")
    parser.add_argument("--query", required=True, help="Query string.")
    parser.add_argument("--top-k", type=int, default=10, help="Maximum number of results to return.")
    parser.add_argument("--source-type", choices=["web_search", "web_search_mock", "repository"], 
                        help="Filter by source type.")
    args = parser.parse_args()
    
    # Query the index
    results = query_firecrawl_content(
        query=args.query,
        repo_name=args.repo,
        top_k=args.top_k,
        filter_source_type=args.source_type
    )
    
    # Print the results
    logger.info(f"Found {len(results)} results for query: {args.query}")
    print(f"\nTop {len(results)} results for query: '{args.query}'")
    print("=" * 80)
    
    for i, result in enumerate(results):
        print(f"Result {i+1} (Score: {result['score']:.4f}):")
        print(f"Text: {result['text'][:500]}...")
        if result.get("url"):
            print(f"URL: {result['url']}")
        if result.get("title"):
            print(f"Title: {result['title']}")
        print(f"Source: {result['source_type']}")
        print("-" * 80)

if __name__ == "__main__":
    main()
