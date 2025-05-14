"""
Pipeline integration module for the repository ingestion pipeline.

This module integrates all components into a cohesive pipeline and provides
the main functionality for the repository ingestion process.
"""

import logging
import os
from typing import Dict, Any, List, Optional

from repo_ingestion.config.config_loader import get_nested_config
from repo_ingestion.git.repo_manager import extract_repo_name, clone_or_update_repo
from repo_ingestion.repomix.processor import (
    execute_repomix, parse_repomix_output, extract_urls_from_repomix_output
)
from repo_ingestion.embedding.embedder import get_embedding_function, embed_chunks
from repo_ingestion.pinecone.index_manager import (
    init_pinecone, ensure_index_exists, prepare_vectors_for_upsert,
    upsert_vectors, get_namespace_for_repo
)
from repo_ingestion.firecrawl.crawler import (
    init_firecrawl, scrape_urls, process_firecrawl_results
)
from repo_ingestion.firecrawl.deep_research import (
    extract_research_topics, perform_deep_research, enrich_content_with_research
)
from repo_ingestion.validation.validation import validate_repository_ingestion

# Configure logging
logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Exception raised for errors in the pipeline."""
    pass


def run_pipeline(args: Any, config: Dict[str, Any], env_vars: Dict[str, str]) -> Dict[str, Any]:
    """
    Run the repository ingestion pipeline.

    Args:
        args: Command-line arguments.
        config: Configuration dictionary.
        env_vars: Environment variables dictionary.

    Returns:
        Dictionary containing the pipeline results.

    Raises:
        PipelineError: If the pipeline fails.
    """
    try:
        # Extract repository name from URL
        repo_url = args.repo_url
        repo_name = extract_repo_name(repo_url)
        
        logger.info(f"Starting pipeline for repository: {repo_name}")
        
        # Step 1: Clone or update repository
        logger.info("Step 1: Clone or update repository")
        repo_path = clone_or_update_repo(repo_url)
        
        # Step 2: Execute Repomix and process output
        logger.info("Step 2: Execute Repomix and process output")
        repomix_output_path = execute_repomix(repo_path)
        repo_chunks = parse_repomix_output(repomix_output_path)
        
        # Step 3: Initialize embedding function
        logger.info("Step 3: Initialize embedding function")
        embedding_function = get_embedding_function(config, env_vars)
        embedding_dimension = get_nested_config(config, "pinecone.dimension")
        
        # Step 4: Initialize Pinecone client and ensure index exists
        logger.info("Step 4: Initialize Pinecone client and ensure index exists")
        pinecone_client = init_pinecone(
            env_vars["PINECONE_API_KEY"],
            env_vars["PINECONE_ENVIRONMENT"]
        )
        
        # Use index name from config if available, otherwise use repository name
        # Ensure we use the actual repository name, not a default value
        default_index_name = f"{repo_name.lower()}-repo"
        index_name = get_nested_config(config, "pinecone.index_name", default_index_name)
        
        # Override the index name if it's the default from config but we're using a different repo
        if index_name == "patchwork-repo" and repo_name.lower() != "patchwork":
            index_name = default_index_name
            
        logger.info(f"Using index name: {index_name}")
        
        index = ensure_index_exists(
            pinecone_client,
            index_name,
            embedding_dimension,
            get_nested_config(config, "pinecone.metric")
        )
        
        # Step 5: Embed and upsert repository content
        logger.info("Step 5: Embed and upsert repository content")
        repo_chunks_with_embeddings = embed_chunks(repo_chunks, embedding_function, embedding_dimension)
        repo_vectors = prepare_vectors_for_upsert(repo_chunks_with_embeddings)
        
        namespace = get_namespace_for_repo(repo_name)
        repo_upsert_results = upsert_vectors(index, repo_vectors, namespace)
        
        # Check if Firecrawl is enabled
        use_firecrawl = not getattr(args, "no_firecrawl", False)
        firecrawl_chunks = []
        search_query = getattr(args, "search_query", None)
        
        # Check if we're in mock mode
        mock_mode = getattr(args, "mock_mode", False)
        
        if use_firecrawl:
            # Step 6: Initialize Firecrawl client
            logger.info("Step 6: Initialize Firecrawl client")
            firecrawl_client = init_firecrawl(env_vars["FIRECRAWL_API_KEY"])
            
            if search_query:
                # If search query is provided, use Firecrawl search instead of URL extraction
                logger.info(f"Step 7: Performing Firecrawl search for query: '{search_query}'")
                
                try:
                    # Import search module
                    logger.info("Importing search_web_content function")
                    from repo_ingestion.firecrawl.search import search_web_content
                    
                    # Combine repository name with search query for better results
                    combined_query = f"{repo_name} {search_query}"
                    logger.info(f"Using combined search query: '{combined_query}'")
                    
                    # Check if Firecrawl client is initialized properly
                    logger.info(f"Firecrawl client type: {type(firecrawl_client)}")
                    
                    # Perform web search
                    logger.info("Executing search_web_content function")
                    logger.info(f"Mock mode: {mock_mode}")
                    firecrawl_results = search_web_content(
                        firecrawl_client=firecrawl_client,
                        query=combined_query,
                        limit=get_nested_config(config, "firecrawl.max_urls", 20),
                        scrape_results=True,
                        mock_mode=mock_mode
                    )
                    
                    logger.info(f"Search completed, got {len(firecrawl_results)} results")
                    logger.info(f"Step 8: Processing search results")
                    firecrawl_chunks = process_firecrawl_results(firecrawl_results)
                    logger.info(f"Processed {len(firecrawl_chunks)} chunks from search results")
                    
                except ImportError as ie:
                    logger.error(f"Failed to import search module: {ie}")
                    firecrawl_chunks = []
                except Exception as e:
                    logger.error(f"Error during Firecrawl search: {e}")
                    firecrawl_chunks = []
            else:
                # Use traditional URL extraction from Repomix output
                logger.info("Step 7: Extract URLs from Repomix output")
                urls = extract_urls_from_repomix_output(repomix_output_path)
                
                # Step 8: Scrape content from URLs
                logger.info("Step 8: Scrape content from URLs")
                firecrawl_results = scrape_urls(firecrawl_client, urls)
                
                # Step 9: Process Firecrawl content
                logger.info("Step 9: Process Firecrawl content")
                firecrawl_chunks = process_firecrawl_results(firecrawl_results)
        else:
            logger.info("Steps 6-9: Firecrawl URL extraction and processing is disabled")
        
        # Step 10: Perform deep research on repository content (if enabled)
        research_results = {}
        use_deep_research = not getattr(args, "no_deep_research", False) and get_nested_config(config, "firecrawl.deep_research.enabled", False)
        
        if use_deep_research and use_firecrawl:
            logger.info("Step 10: Performing deep research on repository content")
            
            # Use search query if provided, otherwise extract topics from repository chunks
            if search_query:
                research_topics = [search_query]
                logger.info(f"Using provided search query for deep research: '{search_query}'")
            else:
                # Extract research topics from repository chunks
                research_topics = extract_research_topics(repo_chunks)
                logger.info(f"Extracted {len(research_topics)} research topics: {research_topics}")
            
            # Perform deep research on topics
            max_depth = get_nested_config(config, "firecrawl.deep_research.max_depth", 3)
            max_urls = get_nested_config(config, "firecrawl.deep_research.max_urls", 10)
            
            try:
                import asyncio
                research_results = asyncio.run(perform_deep_research(
                    topics=research_topics,
                    max_depth=max_depth,
                    max_urls=max_urls
                ))
                
                # Enrich content with research results
                enriched_chunks = enrich_content_with_research(repo_chunks, research_results)
                
                # Embed and upsert enriched content
                enriched_chunks_with_embeddings = embed_chunks(enriched_chunks, embedding_function, embedding_dimension)
                enriched_vectors = prepare_vectors_for_upsert(enriched_chunks_with_embeddings)
                
                # Use a different namespace for enriched content
                enriched_namespace = f"{namespace}-enriched"
                enriched_upsert_results = upsert_vectors(index, enriched_vectors, enriched_namespace)
                logger.info(f"Upserted {enriched_upsert_results.get('total_upserted', 0)} enriched vectors")
            except Exception as e:
                logger.warning(f"Error in deep research: {e}")
                logger.warning("Continuing pipeline without deep research")
        else:
            logger.info("Step 10: Deep research is disabled, skipping")
        
        # Step 11: Embed and upsert Firecrawl content
        firecrawl_upsert_results = {"total_upserted": 0}
        if use_firecrawl and firecrawl_chunks:
            logger.info("Step 11: Embed and upsert Firecrawl content")
            firecrawl_chunks_with_embeddings = embed_chunks(firecrawl_chunks, embedding_function, embedding_dimension)
            firecrawl_vectors = prepare_vectors_for_upsert(firecrawl_chunks_with_embeddings)
            
            firecrawl_upsert_results = upsert_vectors(index, firecrawl_vectors, namespace)
        else:
            logger.info("Step 11: Skipping Firecrawl content upsert (disabled or no chunks)")
        
        # Step 12: Validate repository ingestion
        logger.info("Step 12: Validating repository ingestion")
        repomix_output_path = os.path.join(repo_path, "repomix-output.xml")
        
        try:
            validation_results = validate_repository_ingestion(
                index=index,
                namespace=namespace,
                repo_path=repo_path,
                repomix_output_path=repomix_output_path,
                embedding_dimension=embedding_dimension
            )
            
            success_rate = validation_results.get('success_rate', 0)
            found_count = validation_results.get('found_count', 0)
            total_count = validation_results.get('total_count', 0)
            results = validation_results.get('results', [])
            
            if validation_results.get("success", False):
                logger.info(f"Validation successful: {success_rate * 100:.2f}% of files found ({found_count}/{total_count})")
            else:
                logger.warning(f"Validation failed: {success_rate * 100:.2f}% of files found ({found_count}/{total_count})")
                if 'error' in validation_results:
                    logger.warning(f"Validation error: {validation_results.get('error')}")
            
            # Log details about found and not found files
            if results:
                found_files = [r.get('file_path') for r in results if r.get('found', False)]
                not_found_files = [r.get('file_path') for r in results if not r.get('found', False)]
                
                if found_files:
                    logger.info(f"Found files: {', '.join(found_files)}")
                if not_found_files:
                    logger.warning(f"Not found files: {', '.join(not_found_files)}")
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            validation_results = {
                "success": False,
                "error": str(e)
            }
        
        # Step 13: Report results
        logger.info("Step 13: Report results")
        total_upserted = repo_upsert_results.get("total_upserted", 0) + firecrawl_upsert_results.get("total_upserted", 0)
        
        logger.info(f"Pipeline completed successfully for repository: {repo_name}")
        logger.info(f"Total vectors upserted: {total_upserted}")
        
        results = {
            "repository": repo_name,
            "index_name": index_name,
            "namespace": namespace,
            "repo_chunks": len(repo_chunks),
            "repo_vectors_upserted": repo_upsert_results.get("total_upserted", 0),
            "total_vectors_upserted": repo_upsert_results.get("total_upserted", 0),
            "validation_results": validation_results
        }
        
        # Add Firecrawl results if enabled
        if use_firecrawl:
            results.update({
                "urls_extracted": len(urls) if 'urls' in locals() else 0,
                "firecrawl_chunks": len(firecrawl_chunks),
                "firecrawl_vectors_upserted": firecrawl_upsert_results.get("total_upserted", 0),
                "total_vectors_upserted": results["total_vectors_upserted"] + firecrawl_upsert_results.get("total_upserted", 0)
            })
        
        # Add deep research results if enabled
        if use_deep_research and use_firecrawl:
            results["deep_research_topics"] = len(research_results) if research_results else 0
        
        return results
    except Exception as e:
        logger.error(f"Error in pipeline: {e}")
        raise PipelineError(f"Error in pipeline: {e}")
