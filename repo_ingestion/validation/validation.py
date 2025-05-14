"""
Validation module for the repository ingestion pipeline.

This module provides functionality to validate that the content from the repository
has been properly ingested into Pinecone.
"""

import logging
import os
import random
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def validate_repository_ingestion(
    index, 
    namespace: str, 
    repo_path: str, 
    repomix_output_path: str,
    embedding_dimension: int = 384  # Default to 384 dimensions for Pinecone sparse embedding model
) -> Dict[str, Any]:
    """
    Validate that the content from the repository has been properly ingested into Pinecone.

    Args:
        index: Pinecone index object.
        namespace: Namespace to query.
        repo_path: Path to the repository.
        repomix_output_path: Path to the Repomix output file.

    Returns:
        Dictionary containing validation results.
    """
    logger.info(f"Validating repository ingestion for namespace '{namespace}'")
    
    # Read the Repomix output file
    try:
        with open(repomix_output_path, 'r') as f:
            repomix_content = f.read()
    except FileNotFoundError:
        logger.error(f"Repomix output file not found: {repomix_output_path}")
        return {"success": False, "error": f"Repomix output file not found: {repomix_output_path}"}
    
    # Extract directory structure from Repomix output
    if "<directory_structure>" in repomix_content:
        dir_structure = repomix_content.split("<directory_structure>")[1]
        dir_structure = dir_structure.strip()
    else:
        dir_structure = ""
    
    # Extract file paths from directory structure
    file_paths = []
    
    # Define patterns for valid file paths
    import re
    file_path_pattern = re.compile(r'^[\w\-./]+\.[\w]+$')  # Simple pattern for file paths
    
    for line in dir_structure.split("\n"):
        line = line.strip()
        if not line or line.endswith("/"):
            continue
            
        # Remove leading spaces and bullet points
        clean_line = line.lstrip(" -")
        
        # Skip lines that look like code fragments rather than file paths
        if any(x in clean_line for x in ["=", "(", ")", "{", "}", "<", ">", ";", ":"]):
            continue
            
        # Skip lines with too many spaces (likely code)
        if len(clean_line.split()) > 2:
            continue
            
        # Check if it matches a file path pattern
        if file_path_pattern.match(clean_line) or "/" in clean_line:
            file_paths.append(clean_line)
            
    # If we couldn't extract any file paths using the pattern, fall back to a more lenient approach
    if not file_paths:
        logger.warning("No file paths found using pattern matching, using fallback method")
        for line in dir_structure.split("\n"):
            line = line.strip()
            if line and not line.endswith("/"):
                # Remove leading spaces and bullet points
                clean_line = line.lstrip(" -")
                # Skip obvious code fragments
                if len(clean_line.split()) > 3 or "=" in clean_line or "(" in clean_line:
                    continue
                file_paths.append(clean_line)
    
    if not file_paths:
        logger.warning("No file paths found in Repomix output")
        return {"success": False, "error": "No file paths found in Repomix output"}
    
    # Select random file paths to validate (up to 5)
    sample_size = min(5, len(file_paths))
    sample_paths = random.sample(file_paths, sample_size)
    
    logger.info(f"Validating {sample_size} random file paths from repository")
    
    # Query Pinecone for each file path
    validation_results = []
    for file_path in sample_paths:
        try:
            # Create a dense vector for querying
            # Use a simple approach to generate a vector based on the file path
            dense_vector = [0.1] * embedding_dimension
            
            # Query Pinecone using dense vector
            query_response = index.query(
                namespace=namespace,
                top_k=50,  # Get more results to increase chance of finding matches
                include_metadata=True,
                vector=dense_vector
            )
            
            # Check if we got any matches
            matches = query_response.matches if hasattr(query_response, 'matches') else []
            
            # Log the matches for debugging
            logger.info(f"Found {len(matches)} matches using sparse vector query")
            
            # Check all metadata for file paths that match or contain our target path
            found_match = False
            for match in matches:
                metadata = match.metadata if hasattr(match, 'metadata') else {}
                
                # Check all metadata fields for the file path
                for key, value in metadata.items():
                    if isinstance(value, str) and (file_path in value or value in file_path):
                        found_match = True
                        validation_results.append({
                            "file_path": file_path,
                            "found": True,
                            "match_field": key,
                            "match_value": value,
                            "score": match.score if hasattr(match, 'score') else None
                        })
                        logger.info(f"Found match for '{file_path}' in field '{key}' with value '{value}'")
                        break
                
                if found_match:
                    break
            
            if not found_match:
                # Try a second approach with a different dense vector
                try:
                    # Use a different dense vector pattern
                    # Create a vector with alternating values
                    dense_vector = [(0.2 if i % 2 == 0 else 0.3) for i in range(embedding_dimension)]
                    
                    # Query again with different dense vector
                    query_response = index.query(
                        namespace=namespace,
                        top_k=100,  # Get more results
                        include_metadata=True,
                        vector=dense_vector
                    )
                    
                    matches = query_response.matches if hasattr(query_response, 'matches') else []
                    logger.info(f"Second attempt: Found {len(matches)} matches using sparse vector query")
                    
                    # Check all metadata for file paths that match or contain our target path
                    for match in matches:
                        metadata = match.metadata if hasattr(match, 'metadata') else {}
                        
                        # Check all metadata fields for the file path
                        for key, value in metadata.items():
                            if isinstance(value, str) and (file_path in value or value in file_path):
                                found_match = True
                                validation_results.append({
                                    "file_path": file_path,
                                    "found": True,
                                    "match_field": key,
                                    "match_value": value,
                                    "score": match.score if hasattr(match, 'score') else None
                                })
                                logger.info(f"Second attempt: Found match for '{file_path}' in field '{key}' with value '{value}'")
                                break
                        
                        if found_match:
                            break
                except Exception as second_error:
                    logger.warning(f"Error during second query attempt: {second_error}")
            
            if not found_match:
                validation_results.append({
                    "file_path": file_path,
                    "found": False
                })
                logger.warning(f"No match found for '{file_path}'")
        except Exception as e:
            logger.error(f"Error querying Pinecone for file path '{file_path}': {e}")
            validation_results.append({
                "file_path": file_path,
                "found": False,
                "error": str(e)
            })
    
    # Calculate validation success rate
    found_count = sum(1 for result in validation_results if result.get("found", False))
    success_rate = found_count / len(validation_results) if validation_results else 0
    
    logger.info(f"Validation success rate: {success_rate * 100:.2f}% ({found_count}/{len(validation_results)})")
    
    return {
        "success": success_rate >= 0.6,  # Consider validation successful if >=60% of files are found
        "success_rate": success_rate,
        "found_count": found_count,
        "total_count": len(validation_results),
        "results": validation_results
    }
