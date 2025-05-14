#!/usr/bin/env python
"""
Script to test the Firecrawl SDK with the API key from the .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"No .env file found at {env_path}")

# Check if the API key is loaded
firecrawl_api_key = os.environ.get('FIRECRAWL_API_KEY')
if firecrawl_api_key:
    print(f"FIRECRAWL_API_KEY found: {firecrawl_api_key[:5]}...{firecrawl_api_key[-5:]}")
else:
    print("FIRECRAWL_API_KEY not found in environment variables")
    sys.exit(1)

# Try to import the Firecrawl SDK
try:
    import firecrawl
    print(f"Successfully imported Firecrawl SDK version {firecrawl.__version__}")
except ImportError as e:
    print(f"Failed to import Firecrawl SDK: {e}")
    sys.exit(1)

# Try to create a Firecrawl client
try:
    # Based on the available classes, FirecrawlApp seems to be the main client class
    client = firecrawl.FirecrawlApp(api_key=firecrawl_api_key)
    print("Successfully created Firecrawl client using FirecrawlApp")
except Exception as e:
    print(f"Failed to create Firecrawl client: {e}")
    sys.exit(1)

# Try to perform a search
try:
    print("\nTesting search functionality...")
    # Check available methods
    print(f"Available methods: {[method for method in dir(client) if not method.startswith('_')]}")
    
    # Try to use the search method if available
    if hasattr(client, 'search'):
        print("Using client.search method...")
        search_results = client.search(query="configuration management best practices", limit=3)
        print(f"Search successful! Found results: {search_results}")
        
        # Print the first result if available
        if hasattr(search_results, '__len__') and len(search_results) > 0:
            first_result = search_results[0]
            print(f"\nFirst result:")
            print(f"Result data: {first_result}")
    else:
        print("Search method not available directly on client")
        # Try alternative approaches
        print("Checking for other search-related methods...")
        for method in dir(client):
            if 'search' in method.lower() and not method.startswith('_'):
                print(f"Found potential search method: {method}")
                try:
                    search_method = getattr(client, method)
                    print(f"Trying {method}...")
                    result = search_method(query="configuration management best practices", limit=3)
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Error with {method}: {e}")
        
        # If no search method is found, try the module-level functions
        print("Checking for module-level search function...")
        if hasattr(firecrawl.firecrawl, 'search'):
            print("Using firecrawl.firecrawl.search...")
            search_results = firecrawl.firecrawl.search(
                api_key=firecrawl_api_key,
                query="configuration management best practices", 
                limit=3
            )
            print(f"Search successful! Results: {search_results}")
        else:
            print("No module-level search function found")
except Exception as e:
    print(f"Search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll tests passed successfully!")
