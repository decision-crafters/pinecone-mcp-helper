"""
Pinecone integration module for the repository ingestion pipeline.

This module provides functionality to connect to Pinecone, create or use an existing index,
and upsert vectors with appropriate metadata and namespace.
"""

import logging
import time
import uuid
from typing import List, Dict, Any, Optional

import pinecone
from pinecone.grpc import PineconeGRPC
from pinecone import ServerlessSpec

# Configure logging
logger = logging.getLogger(__name__)


class PineconeError(Exception):
    """Exception raised for errors in Pinecone operations."""
    pass


def init_pinecone(api_key: str, environment: str):
    """
    Initialize the Pinecone client.

    Args:
        api_key: Pinecone API key.
        environment: Pinecone environment.

    Returns:
        Initialized Pinecone client.

    Raises:
        PineconeError: If initialization fails.
    """
    logger.info(f"Initializing Pinecone client (environment: {environment})")
    
    # Check if this is a mock API key for testing
    if api_key.startswith("mock_"):
        logger.info("Using mock Pinecone client for testing")
        return MockPinecone()
    
    try:
        # Initialize Pinecone client using GRPC (newer SDK version)
        pc = PineconeGRPC(api_key=api_key)
        
        logger.info("Pinecone client initialized successfully using GRPC")
        
        return pc
    except Exception as e:
        logger.error(f"Error initializing Pinecone client: {e}")
        raise PineconeError(f"Error initializing Pinecone client: {e}")


class MockPinecone:
    """Mock Pinecone client for testing purposes."""
    
    def __init__(self):
        self.indexes = {}
    
    def list_indexes(self):
        """List mock indexes."""
        # Return a list of mock index objects with a name attribute
        class MockIndexInfo:
            def __init__(self, name):
                self.name = name
        
        return [MockIndexInfo(name) for name in self.indexes.keys()]
    
    def create_index(self, name, dimension, metric, spec=None):
        """Create a mock index."""
        logger.info(f"Creating mock index: {name}")
        self.indexes[name] = MockIndex(name, dimension, metric)
        return True
    
    def Index(self, name):
        """Get a mock index."""
        if name not in self.indexes:
            logger.info(f"Creating mock index on demand: {name}")
            self.indexes[name] = MockIndex(name, 384, "cosine")
        return self.indexes[name]


class MockIndex:
    """Mock Pinecone index for testing purposes."""
    
    def __init__(self, name, dimension, metric):
        self.name = name
        self.dimension = dimension
        self.metric = metric
        self.namespaces = {}
    
    def upsert(self, vectors, namespace=""):
        """Upsert vectors to the mock index."""
        if namespace not in self.namespaces:
            self.namespaces[namespace] = {}
        
        # Store vectors in the namespace
        for vector in vectors:
            vector_id = vector.get("id")
            if vector_id:
                self.namespaces[namespace][vector_id] = vector
        
        return {"upserted_count": len(vectors)}


def ensure_index_exists(client, index_name: str, dimension: int, metric: str):
    """
    Ensure that a Pinecone index with the specified name exists.
    If it doesn't exist, create it with the specified parameters.

    Args:
        client: Initialized Pinecone client.
        index_name: Name of the index.
        dimension: Dimension of the vectors.
        metric: Similarity metric to use (e.g., 'cosine', 'dotproduct', 'euclidean').

    Returns:
        Pinecone index object.

    Raises:
        PineconeError: If index creation fails or the existing index has incompatible parameters.
    """
    logger.info(f"Ensuring index exists: {index_name}")
    
    # Check if we're using a mock client
    if isinstance(client, MockPinecone):
        logger.info(f"Using mock Pinecone client for index: {index_name}")
        return client.Index(index_name)
    
    try:
        # Check if index exists
        indexes = client.list_indexes()
        index_names = [index.name for index in indexes]
        
        if index_name in index_names:
            logger.info(f"Index {index_name} already exists")
            
            # Get index
            index = client.Index(index_name)
            
            # TODO: Validate index parameters (dimension, metric)
            # This requires fetching index stats and validating them
            
            return index
        else:
            logger.info(f"Creating new serverless index: {index_name} (dimension: {dimension}, metric: {metric})")
            
            # Create serverless index using ServerlessSpec
            client.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            time.sleep(10)  # Simple wait, could be replaced with polling
            
            # Get index
            index = client.Index(index_name)
            
            logger.info(f"Index {index_name} created successfully")
            
            return index
    except Exception as e:
        logger.error(f"Error ensuring index exists: {e}")
        raise PineconeError(f"Error ensuring index exists: {e}")


def generate_vector_id(prefix: str = "") -> str:
    """
    Generate a unique ID for a vector.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        Unique ID string.
    """
    # Generate a UUID
    unique_id = str(uuid.uuid4())
    
    # Add prefix if provided
    if prefix:
        return f"{prefix}-{unique_id}"
    else:
        return unique_id


def prepare_vectors_for_upsert(chunks_with_embeddings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare vectors for upserting to Pinecone.

    Args:
        chunks_with_embeddings: List of dictionaries, each containing a text chunk with metadata and embedding.

    Returns:
        List of dictionaries in the format expected by Pinecone's upsert method.
    """
    import json
    
    # Pinecone metadata size limit (40KB)
    MAX_METADATA_SIZE = 40 * 1024
    vectors = []
    
    for chunk in chunks_with_embeddings:
        # Extract embedding and metadata
        embedding = chunk.get("embedding", [])
        
        # Create metadata dictionary
        metadata = {
            "source_type": chunk.get("source_type", "unknown")
        }
        
        # Add file_path or source_url to metadata based on source_type
        if chunk.get("source_type") == "repository" and "file_path" in chunk:
            metadata["file_path"] = chunk["file_path"]
        elif chunk.get("source_type") == "firecrawl" and "source_url" in chunk:
            metadata["source_url"] = chunk["source_url"]
        
        # Get the text content
        text = chunk.get("text", "")
        
        # Calculate current metadata size
        metadata_size = len(json.dumps(metadata).encode('utf-8'))
        
        # Calculate how much space we have left for the text
        available_space = MAX_METADATA_SIZE - metadata_size - 10  # 10 bytes buffer
        
        # Truncate text if necessary to fit within metadata size limit
        if len(text.encode('utf-8')) > available_space:
            # Truncate text to fit within available space
            # This is a simple approach that may break UTF-8 characters
            # A more sophisticated approach would be to truncate at character boundaries
            truncated_text = text.encode('utf-8')[:available_space].decode('utf-8', errors='ignore')
            metadata["text"] = truncated_text
            metadata["truncated"] = True
            logger.warning(f"Text truncated from {len(text)} to {len(truncated_text)} characters to fit metadata size limit")
        else:
            metadata["text"] = text
        
        # Generate a unique ID for the vector
        vector_id = generate_vector_id(chunk.get("source_type", ""))
        
        # Create vector dictionary
        vector = {
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        }
        
        vectors.append(vector)
    
    return vectors


def upsert_vectors(index: pinecone.Index, vectors: List[Dict[str, Any]], namespace: str, batch_size: int = 100) -> Dict[str, Any]:
    """
    Upsert vectors to a Pinecone index.

    Args:
        index: Pinecone index object.
        vectors: List of vectors to upsert.
        namespace: Namespace to upsert vectors to.
        batch_size: Number of vectors to upsert in a single batch.

    Returns:
        Dictionary containing the upsert results.

    Raises:
        PineconeError: If upserting fails.
    """
    logger.info(f"Upserting {len(vectors)} vectors to namespace '{namespace}'")
    
    try:
        # Upsert vectors in batches
        total_upserted = 0
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            # Upsert batch
            upsert_response = index.upsert(
                vectors=batch,
                namespace=namespace
            )
            
            # Update total upserted
            # Handle different response formats (GRPC vs REST)
            if hasattr(upsert_response, 'get'):
                # REST API response format
                batch_upserted = upsert_response.get("upserted_count", len(batch))
            elif hasattr(upsert_response, 'upserted_count'):
                # GRPC API response format
                batch_upserted = upsert_response.upserted_count
            else:
                # Fallback - assume all vectors were upserted
                logger.warning("Could not determine upserted count from response, assuming all vectors were upserted")
                batch_upserted = len(batch)
            
            total_upserted += batch_upserted
            
            # Log progress
            logger.info(f"Upserted batch {i // batch_size + 1}/{(len(vectors) + batch_size - 1) // batch_size} ({total_upserted}/{len(vectors)} vectors)")
        
        logger.info(f"Successfully upserted {total_upserted}/{len(vectors)} vectors to namespace '{namespace}'")
        
        return {"total_upserted": total_upserted}
    except Exception as e:
        logger.error(f"Error upserting vectors: {e}")
        raise PineconeError(f"Error upserting vectors: {e}")


def get_namespace_for_repo(repo_name: str) -> str:
    """
    Get the namespace to use for a repository.

    Args:
        repo_name: Name of the repository.

    Returns:
        Namespace string.
    """
    return f"{repo_name}-code"
