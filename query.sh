#!/bin/bash

# Query script for the repository ingestion pipeline
# This script provides a convenient way to query the Pinecone index for repository content

# Set default values
CONFIG_FILE="config.yaml"
TOP_K=5

# Display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo ""
    echo "This script queries the Pinecone index for repository content."
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message and exit"
    echo "  --repo REPO            Repository name to query (required)"
    echo "  --query QUERY          Query string (required)"
    echo "  --top-k N              Number of results to return (default: 5)"
    echo "  --config FILE          Path to the configuration file (default: config.yaml)"
    echo ""
    echo "Example:"
    echo "  $0 --repo patchwork --query \"How does the PR review feature work?\""
    echo "  $0 --repo kanbn --query \"task management\" --top-k 10"
    echo ""
    echo "Notes:"
    echo "  - The Firecrawl search and deep research features are still in testing."
    echo "  - Search results may include both repository content and web content."
    echo "  - For best results, use specific queries related to the repository."
    echo ""
    exit 1
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --query)
            QUERY="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --top-k)
            TOP_K="$2"
            shift 2
            ;;
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check for required arguments
if [ -z "$REPO" ] || [ -z "$QUERY" ]; then
    echo "Error: Repository name and query text are required"
    show_usage
fi

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run bootstrap.sh first to set up the environment."
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if the .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please create a .env file with your API keys."
    exit 1
fi

# Run the query
echo "Querying repository: $REPO"
echo "Query: \"$QUERY\""
echo "Top-k: $TOP_K"
echo

# Set protobuf environment variable to fix compatibility issue
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

python -m repo_ingestion.query --repo "$REPO" --query "$QUERY" --top-k "$TOP_K" --config "$CONFIG_FILE"

# Deactivate the virtual environment
deactivate

echo
echo "Query completed"
