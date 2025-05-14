#!/usr/bin/env python
"""
Script to check if Firecrawl MCP functions are available in the current environment.
"""

import sys
import os

def check_mcp_functions():
    """Check if Firecrawl MCP functions are available."""
    print("Checking for Firecrawl MCP functions...")
    
    # Check for environment variables
    firecrawl_api_key = os.environ.get('FIRECRAWL_API_KEY')
    print(f"FIRECRAWL_API_KEY present: {bool(firecrawl_api_key)}")
    
    # Check for MCP functions in main module
    main_module = sys.modules['__main__']
    main_dir = dir(main_module)
    
    print("\nChecking for MCP functions in main module:")
    for func_name in ['mcp1_firecrawl_search', 'mcp1_firecrawl_scrape', 'mcp1_firecrawl_crawl']:
        print(f"  {func_name} available: {func_name in main_dir}")
    
    # Check for MCP functions in global namespace
    print("\nChecking for MCP functions in global namespace:")
    for func_name in ['mcp1_firecrawl_search', 'mcp1_firecrawl_scrape', 'mcp1_firecrawl_crawl']:
        print(f"  {func_name} available: {func_name in globals()}")
    
    # Try to import MCP functions
    print("\nTrying to import MCP functions:")
    try:
        import mcp1_firecrawl_search
        print("  Successfully imported mcp1_firecrawl_search")
    except ImportError as e:
        print(f"  Failed to import mcp1_firecrawl_search: {e}")
    
    try:
        import mcp1_firecrawl_scrape
        print("  Successfully imported mcp1_firecrawl_scrape")
    except ImportError as e:
        print(f"  Failed to import mcp1_firecrawl_scrape: {e}")

if __name__ == "__main__":
    check_mcp_functions()
