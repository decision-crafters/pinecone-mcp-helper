#!/usr/bin/env python3
"""
Script to validate Firecrawl integration by directly querying the Pinecone index
for content with specific source types.
"""

import os
import argparse
import logging
from dotenv import load_dotenv

from repo_ingestion.pinecone.index_manager import init_pinecone
from repo_ingestion.embedding.embedder import get_embedding_function

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to validate Firecrawl integration."""
    parser = argparse.ArgumentParser(description="Validate Firecrawl integration")
    parser.add_argument("--repo", type=str, required=True, help="Repository name")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment variables
    required_env_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_env_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_env_vars)}")
        return 1
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=os.environ.get("PINECONE_API_KEY"),
        environment=os.environ.get("PINECONE_ENVIRONMENT")
    )
    
    # Get index name
    index_name = f"{args.repo}-repo"
    
    # Get namespace
    namespace = f"{args.repo}-code"
    
    # Get the index
    index = pinecone_client.Index(index_name)
    
    # Create a simple embedding function for metadata filtering
    embedding_function = get_embedding_function(
        config={"embedding": {"model": "pinecone-sparse-english-v0"}},
        env_vars={"EMBEDDING_API_KEY": os.environ.get("EMBEDDING_API_KEY")}
    )
    
    # Create a dummy query embedding
    query_embedding = embedding_function("web content")
    
    # Query the index with metadata filter for Firecrawl content
    try:
        # First try with web_search source type
        query_response = index.query(
            namespace=namespace,
            top_k=args.top_k,
            include_metadata=True,
            vector=query_embedding,
            filter={"source_type": {"$eq": "web_search"}}
        )
        
        results = []
        matches = query_response.matches if hasattr(query_response, 'matches') else []
        
        if not matches:
            # Try with web_search_mock source type
            logger.info("No results found with source_type=web_search, trying web_search_mock")
            query_response = index.query(
                namespace=namespace,
                top_k=args.top_k,
                include_metadata=True,
                vector=query_embedding,
                filter={"source_type": {"$eq": "web_search_mock"}}
            )
            matches = query_response.matches if hasattr(query_response, 'matches') else []
        
        # Process the results
        for match in matches:
            result = {
                "score": match.score if hasattr(match, 'score') else None,
                "id": match.id if hasattr(match, 'id') else None,
                "metadata": match.metadata if hasattr(match, 'metadata') else {}
            }
            results.append(result)
        
        # Print the results
        if results:
            print(f"\nFound {len(results)} Firecrawl results in the Pinecone index")
            print("=" * 80)
            for i, result in enumerate(results):
                print(f"Result {i+1} (Score: {result['score']:.4f}):")
                
                # Print metadata
                metadata = result.get("metadata", {})
                if "text" in metadata:
                    # Truncate text if too long
                    text = metadata["text"]
                    if len(text) > 500:
                        text = text[:500] + "..."
                    print(f"Text: {text}")
                
                if "url" in metadata:
                    print(f"URL: {metadata['url']}")
                
                if "title" in metadata:
                    print(f"Title: {metadata['title']}")
                
                if "source_type" in metadata:
                    print(f"Source: {metadata['source_type']}")
                
                print("-" * 80)
        else:
            print(f"No Firecrawl content found in the index for repository: {args.repo}")
            print("This could mean either:")
            print("1. The Firecrawl integration is not working correctly")
            print("2. No Firecrawl content was ingested (check if --search-query was used)")
            print("3. The content is stored with a different source_type")
    
    except Exception as e:
        logger.error(f"Error querying index: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
