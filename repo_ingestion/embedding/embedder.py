"""
Embedding module for the repository ingestion pipeline.

This module provides functionality to convert text chunks into vector embeddings
using various embedding models.
"""

import logging
import requests
from typing import List, Dict, Any, Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Exception raised for errors in the embedding process."""
    pass


def get_embedding_function(config: Dict[str, Any], env_vars: Dict[str, str]) -> Callable[[str], List[float]]:
    """
    Get an embedding function based on the configuration.

    Args:
        config: Configuration dictionary.
        env_vars: Environment variables dictionary.

    Returns:
        Callable function that converts text to embeddings.

    Raises:
        ValueError: If the embedding model is not supported or required environment variables are missing.
    """
    model_name = config.get("embedding", {}).get("model", "")
    
    if not model_name:
        raise ValueError("Embedding model not specified in configuration")
    
    logger.info(f"Creating embedding function for model: {model_name}")
    
    # Multilingual E5 Large embedding model
    if model_name == "multilingual-e5-large":
        return create_e5_embedding_function(env_vars.get("EMBEDDING_API_KEY"))
    
    # LLama text embedding model
    elif model_name == "llama-text-embed-v2":
        return create_llama_embedding_function(env_vars.get("EMBEDDING_API_KEY"))
    
    # Pinecone sparse embedding model
    elif model_name == "pinecone-sparse-english-v0":
        return create_pinecone_sparse_embedding_function(env_vars.get("EMBEDDING_API_KEY"))
    
    # Mock embedding model for testing
    elif model_name == "mock_embedding_model":
        return create_mock_embedding_function()
    
    # Add more embedding models as needed
    
    else:
        raise ValueError(f"Unsupported embedding model: {model_name}")


def create_e5_embedding_function(api_key: Optional[str] = None) -> Callable[[str], List[float]]:
    """
    Create an embedding function for the multilingual-e5-large model.

    Args:
        api_key: API key for the embedding service (if required).

    Returns:
        Callable function that converts text to embeddings.
    """
    # Check if API key is required and provided
    if api_key is None:
        logger.warning("No API key provided for E5 embedding model, assuming local model or API that doesn't require authentication")
    
    def embed_text(text: str) -> List[float]:
        """
        Embed text using the multilingual-e5-large model.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding.

        Raises:
            EmbeddingError: If the embedding process fails.
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, you would use the appropriate API or library
            # to generate embeddings using the multilingual-e5-large model
            
            # Example using a hypothetical API
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                "https://api.example.com/embed",
                json={"text": text, "model": "multilingual-e5-large"},
                headers=headers
            )
            
            if response.status_code != 200:
                raise EmbeddingError(f"API request failed with status code {response.status_code}: {response.text}")
            
            embedding = response.json().get("embedding", [])
            
            if not embedding:
                raise EmbeddingError("Empty embedding returned from API")
            
            return embedding
        except requests.RequestException as e:
            raise EmbeddingError(f"Error making API request: {e}")
        except Exception as e:
            raise EmbeddingError(f"Unexpected error during embedding: {e}")
    
    return embed_text


def create_llama_embedding_function(api_key: Optional[str] = None) -> Callable[[str], List[float]]:
    """
    Create an embedding function for the llama-text-embed-v2 model.

    Args:
        api_key: API key for the embedding service (if required).

    Returns:
        Callable function that converts text to embeddings.
    """
    # Similar implementation to create_e5_embedding_function, adjusted for llama-text-embed-v2
    # This is a placeholder implementation
    def embed_text(text: str) -> List[float]:
        # Implementation for llama-text-embed-v2
        # ...
        return []  # Placeholder
    
    return embed_text


def create_pinecone_sparse_embedding_function(api_key: Optional[str] = None) -> Callable[[str], List[float]]:
    """
    Create an embedding function for the pinecone-sparse-english-v0 model.

    Args:
        api_key: API key for the embedding service (if required).

    Returns:
        Callable function that converts text to embeddings.
    """
    import numpy as np
    
    def embed_text(text: str) -> List[float]:
        """
        Embed text using a simple sparse embedding approach.
        
        For testing purposes, this creates a 384-dimensional vector with
        sparse values based on the hash of words in the text.
        
        Args:
            text: Text to embed.
            
        Returns:
            List of floats representing the embedding.
        """
        if not text or not text.strip():
            # Return a zero vector for empty text
            return [0.0] * 384
        
        # Create a sparse vector of dimension 384
        embedding = np.zeros(384)
        
        # Simple word hashing for sparse embedding
        words = text.lower().split()
        for word in words:
            # Hash the word to get an index between 0 and 383
            index = hash(word) % 384
            # Set a non-zero value at this index
            embedding[index] = 1.0
        
        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()
    
    return embed_text


def create_mock_embedding_function() -> Callable[[str], List[float]]:
    """
    Create a mock embedding function for testing purposes.

    Returns:
        Callable function that returns a fixed-size vector of zeros.
    """
    logger.info("Creating mock embedding function for testing")
    
    def embed_text(text: str) -> List[float]:
        """
        Return a mock embedding vector (all zeros).

        Args:
            text: Text to embed (ignored in mock implementation).

        Returns:
            List of 384 zeros representing a mock embedding.
        """
        # Return a fixed-size vector of zeros (dimension 384 is common)
        return [0.0] * 384
    
    return embed_text


def embed_chunks(chunks: List[Dict[str, Any]], embedding_function: Callable[[str], List[float]], dimension: int) -> List[Dict[str, Any]]:
    """
    Embed a list of text chunks.

    Args:
        chunks: List of dictionaries, each containing a text chunk with metadata.
        embedding_function: Function to convert text to embeddings.
        dimension: Expected dimension of the embeddings.

    Returns:
        List of dictionaries, each containing a text chunk with metadata and embedding.

    Raises:
        EmbeddingError: If the embedding process fails or the embedding dimension doesn't match.
    """
    logger.info(f"Embedding {len(chunks)} chunks")
    
    embedded_chunks = []
    
    for i, chunk in enumerate(chunks):
        try:
            text = chunk.get("text", "")
            
            if not text:
                logger.warning(f"Empty text in chunk {i}, skipping")
                continue
            
            # Embed the text
            embedding = embedding_function(text)
            
            # Validate embedding dimension
            if len(embedding) != dimension:
                raise EmbeddingError(f"Embedding dimension mismatch: expected {dimension}, got {len(embedding)}")
            
            # Add embedding to chunk
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = embedding
            
            embedded_chunks.append(chunk_with_embedding)
            
            # Log progress
            if (i + 1) % 100 == 0:
                logger.info(f"Embedded {i + 1}/{len(chunks)} chunks")
        
        except EmbeddingError as e:
            logger.error(f"Error embedding chunk {i}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error embedding chunk {i}: {e}")
            raise EmbeddingError(f"Unexpected error embedding chunk {i}: {e}")
    
    logger.info(f"Successfully embedded {len(embedded_chunks)}/{len(chunks)} chunks")
    
    return embedded_chunks


def batch_embed_chunks(chunks: List[Dict[str, Any]], embedding_function: Callable[[List[str]], List[List[float]]], dimension: int, batch_size: int = 32) -> List[Dict[str, Any]]:
    """
    Embed a list of text chunks in batches.

    Args:
        chunks: List of dictionaries, each containing a text chunk with metadata.
        embedding_function: Function to convert a batch of texts to embeddings.
        dimension: Expected dimension of the embeddings.
        batch_size: Number of chunks to embed in a single batch.

    Returns:
        List of dictionaries, each containing a text chunk with metadata and embedding.

    Raises:
        EmbeddingError: If the embedding process fails or the embedding dimension doesn't match.
    """
    # Implementation for batch embedding
    # This is a placeholder implementation
    return []  # Placeholder
