#!/usr/bin/env python3
"""
Main entry point for the Git repository to Pinecone ingestion pipeline.

This script serves as the main entry point for the pipeline that ingests content
from a Git repository and associated web links into a Pinecone vector database.
"""

import sys
from repo_ingestion.cli import main

if __name__ == "__main__":
    sys.exit(main())
