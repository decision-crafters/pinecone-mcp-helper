"""
Query module for the repository ingestion pipeline.

This module provides functionality to query the Pinecone index for repository content.
"""

# Set protobuf environment variable to fix compatibility issue
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import argparse
import logging
import sys
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from repo_ingestion.config.config_loader import load_config
from repo_ingestion.pinecone.index_manager import init_pinecone, get_namespace_for_repo
from repo_ingestion.embedding.embedder import get_embedding_function

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def query_index(
    index_name: str,
    namespace: str,
    query_text: str,
    top_k: int = 5,
    embedding_function: Optional[Any] = None,
    embedding_dimension: int = 384,
    include_metadata: bool = True,
    pinecone_client: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Query the Pinecone index for repository content.

    Args:
        index_name: Name of the Pinecone index.
        namespace: Namespace to query.
        query_text: Text to search for.
        top_k: Number of results to return.
        embedding_function: Function to embed the query text.
        embedding_dimension: Dimension of the embedding.
        include_metadata: Whether to include metadata in the results.
        pinecone_client: Pinecone client instance.

    Returns:
        List of dictionaries containing the query results.
    """
    logger.info(f"Querying index '{index_name}' in namespace '{namespace}' for: {query_text}")
    
    # Initialize Pinecone client if not provided
    if pinecone_client is None:
        pinecone_client = init_pinecone(
            api_key=os.environ.get("PINECONE_API_KEY"),
            environment=os.environ.get("PINECONE_ENVIRONMENT")
        )
    
    # Get the index
    index = pinecone_client.Index(index_name)
    
    # Get embedding function if not provided
    if embedding_function is None:
        if config is None:
            config = {"embedding": {"model": "pinecone-sparse-english-v0"}}
        if env_vars is None:
            env_vars = {"EMBEDDING_API_KEY": os.environ.get("EMBEDDING_API_KEY")}
        embedding_function = get_embedding_function(
            config=config,
            env_vars=env_vars
        )
    
    # Embed the query text
    query_embedding = embedding_function(query_text)
    
    # Query the index
    try:
        query_response = index.query(
            namespace=namespace,
            top_k=top_k,
            include_metadata=include_metadata,
            vector=query_embedding
        )
        
        # Process the results
        results = []
        matches = query_response.matches if hasattr(query_response, 'matches') else []
        
        for match in matches:
            result = {
                "score": match.score if hasattr(match, 'score') else None,
                "id": match.id if hasattr(match, 'id') else None,
                "metadata": match.metadata if hasattr(match, 'metadata') else {}
            }
            results.append(result)
        
        logger.info(f"Found {len(results)} results for query: {query_text}")
        return results
    except Exception as e:
        logger.error(f"Error querying index: {e}")
        return []


def main():
    """
    Main function for the query module.
    """
    parser = argparse.ArgumentParser(description="Query the Pinecone index for repository content")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--repo", type=str, required=True, help="Repository name")
    parser.add_argument("--query", type=str, required=True, help="Text to search for")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment variables
    required_env_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_env_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_env_vars)}")
        sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error(f"Failed to load configuration from {args.config}")
        sys.exit(1)
    
    # Get index name from config or use default
    index_name = config.get("pinecone", {}).get("index_name", f"{args.repo}-repo")
    
    # Get namespace for repository
    namespace = get_namespace_for_repo(args.repo)
    
    # Get embedding model from config
    embedding_model = config.get("embedding", {}).get("model", "pinecone-sparse-english-v0")
    
    # Get embedding dimension from config
    embedding_dimension = config.get("embedding", {}).get("dimension", 384)
    
    # Create config and env_vars dictionaries for the embedding function
    embedding_config = {"embedding": {"model": embedding_model}}
    embedding_env_vars = {"EMBEDDING_API_KEY": os.environ.get("EMBEDDING_API_KEY")}
    
    # Initialize embedding function
    embedding_function = get_embedding_function(
        config=embedding_config,
        env_vars=embedding_env_vars
    )
    
    # Query the index
    results = query_index(
        index_name=index_name,
        namespace=namespace,
        query_text=args.query,
        top_k=args.top_k,
        embedding_function=embedding_function,
        embedding_dimension=embedding_dimension
    )
    
    # Print the results
    if results:
        print(f"\nTop {len(results)} results for query: '{args.query}'")
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
            
            if "file_path" in metadata:
                print(f"File: {metadata['file_path']}")
            
            if "source_type" in metadata:
                print(f"Source: {metadata['source_type']}")
            
            print("-" * 80)
    else:
        print(f"No results found for query: '{args.query}'")


if __name__ == "__main__":
    main()
