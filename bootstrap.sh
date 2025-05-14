#!/bin/bash
# bootstrap.sh - Real-world Git Repository to Pinecone Ingestion Pipeline
# 
# This script processes a Git repository and ingests its content
# into a Pinecone vector database using our pipeline.

set -e  # Exit immediately if a command exits with a non-zero status

# Color codes for output formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1"
    echo "------------------------------------------------------------"
}

# Function to handle errors
handle_error() {
    log_error "An error occurred at line $1"
    # If we're in a virtual environment, deactivate it
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null || true
    fi
    exit 1
}

# Function to display usage information
show_usage() {
    echo "Usage: $0 [options] [repository_url]"
    echo ""
    echo "This script processes a Git repository and ingests its content"
    echo "into a Pinecone vector database using our pipeline."
    echo ""
    echo "Arguments:"
    echo "  repository_url         URL of the Git repository to process (optional)"
    echo "                         Default: https://github.com/decision-crafters/patchwork.git"
    echo ""
    echo "Options:"
    echo "  -h, --help             Show this help message and exit"
    echo "  -v, --verbose          Enable verbose output"
    echo "  -m, --mock             Use mock services for testing (no actual API calls)"
    echo "  --no-firecrawl         Disable Firecrawl URL extraction and processing"
    echo "  --no-deep-research     Disable deep research on extracted topics"
    echo "  --search-query=QUERY   Specify a search query for Firecrawl and deep research"
    echo "                         (will override automatic topic extraction)"
    echo ""
    echo "Environment Variables:"
    echo "  PINECONE_API_KEY       Pinecone API key"
    echo "  PINECONE_ENVIRONMENT   Pinecone environment"
    echo "  FIRECRAWL_API_KEY      Firecrawl API key"
    echo "  EMBEDDING_API_KEY      Embedding API key"
    echo ""
    echo "Example:"
    echo "  $0 https://github.com/decision-crafters/patchwork.git"
    echo "  $0 --mock https://github.com/decision-crafters/patchwork.git"
    echo ""
}

# Parse command line arguments
VERBOSE=false
USE_MOCK=false
USE_FIRECRAWL=true  # Default: use Firecrawl
USE_DEEP_RESEARCH=true  # Default: use deep research
SEARCH_QUERY=""  # Default: no search query
REPO_URL="https://github.com/decision-crafters/patchwork.git"  # Default repository URL

# Function to extract repository name from URL
extract_repo_name() {
    local url=$1
    local repo_name
    
    # Remove .git extension if present
    url=${url%.git}
    
    # Extract the last part of the URL (the repository name)
    repo_name=$(basename "$url")
    
    echo "$repo_name"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--mock)
            USE_MOCK=true
            shift
            ;;
        --no-firecrawl)
            USE_FIRECRAWL=false
            shift
            ;;
        --no-deep-research)
            USE_DEEP_RESEARCH=false
            shift
            ;;
        --search-query=*)
            SEARCH_QUERY="${1#*=}"
            shift
            ;;
        http*|git@*)
            # This looks like a repository URL
            REPO_URL="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Extract repository name from URL
REPO_NAME=$(extract_repo_name "$REPO_URL")

log_info "Using repository URL: $REPO_URL"
log_info "Repository name: $REPO_NAME"
if [ "$USE_MOCK" = true ]; then
    log_info "Using mock services for testing (no actual API calls)"
fi
if [ "$USE_FIRECRAWL" = false ]; then
    log_info "Firecrawl URL extraction and processing is disabled"
fi
if [ "$USE_DEEP_RESEARCH" = false ]; then
    log_info "Deep research on extracted topics is disabled"
fi
if [ -n "$SEARCH_QUERY" ]; then
    log_info "Using search query: \"$SEARCH_QUERY\""
    log_warn "⚠️  Firecrawl search features are still in testing and may not work as expected. Results may vary."
fi

# Set up error trap
trap 'handle_error $LINENO' ERR

# Print header
echo "============================================================"
log_info "Git Repository to Pinecone Ingestion Pipeline"
echo "============================================================"

# Step 1: Check environment prerequisites
log_step "Checking environment prerequisites"

# Check Python version
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    log_info "Found Python 3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    PYTHON_CMD="python3"
    log_info "Found Python $PYTHON_VERSION"
    
    # Check if Python version is at least 3.8
    if [[ $(echo "$PYTHON_VERSION" | cut -d. -f1) -lt 3 || ($(echo "$PYTHON_VERSION" | cut -d. -f1) -eq 3 && $(echo "$PYTHON_VERSION" | cut -d. -f2) -lt 8) ]]; then
        log_error "Python version must be at least 3.8"
        exit 1
    fi
else
    log_error "Python 3 not found. Please install Python 3.8 or higher"
    exit 1
fi

# Check Git installation
if ! command -v git &> /dev/null; then
    log_error "Git not found. Please install Git"
    exit 1
fi
log_info "Git is installed"

# Check for Repomix installation
if ! command -v repomix &> /dev/null; then
    log_warn "Repomix not found in PATH. Make sure it's installed and available before proceeding."
fi

# Check for required files
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found. Make sure you're running this script from the project root directory"
    exit 1
fi

if [ ! -f "main.py" ]; then
    log_error "main.py not found. Make sure you're running this script from the project root directory"
    exit 1
fi

if [ ! -d "repo_ingestion" ]; then
    log_error "repo_ingestion directory not found. Make sure you're running this script from the project root directory"
    exit 1
fi

log_info "All prerequisites satisfied"

# Step 2: Set up virtual environment
log_step "Setting up virtual environment"

# Create a virtual environment if it doesn't exist
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment in $VENV_DIR"
    $PYTHON_CMD -m venv $VENV_DIR
else
    log_info "Using existing virtual environment in $VENV_DIR"
fi

# Activate the virtual environment
log_info "Activating virtual environment"
source "$VENV_DIR/bin/activate"

# Upgrade pip
log_info "Upgrading pip"
pip install --upgrade pip

# Install dependencies
log_info "Installing dependencies from requirements.txt"
pip install -r requirements.txt

# Check if uvx is available for building requirements
if command -v uvx &> /dev/null; then
    log_info "Using uvx to install requirements"
    uvx pip install -r requirements.txt
else
    log_info "uvx not found, using standard pip to install requirements"
    pip install -r requirements.txt
fi

# Step 3: Check and load API keys
log_step "Checking API keys"

# Source .env file if it exists
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env file"
    source .env
fi

# Check for required API keys
if [ -z "$PINECONE_API_KEY" ]; then
    log_error "PINECONE_API_KEY is not set. Please set it in your environment or .env file"
    exit 1
fi
log_info "PINECONE_API_KEY is set"

if [ -z "$PINECONE_ENVIRONMENT" ]; then
    log_error "PINECONE_ENVIRONMENT is not set. Please set it in your environment or .env file"
    exit 1
fi
log_info "PINECONE_ENVIRONMENT is set"

if [ -z "$FIRECRAWL_API_KEY" ]; then
    log_error "FIRECRAWL_API_KEY is not set. Please set it in your environment or .env file"
    exit 1
fi
log_info "FIRECRAWL_API_KEY is set"

# EMBEDDING_API_KEY is optional, but we'll check if it's set
if [ -z "$EMBEDDING_API_KEY" ]; then
    log_warn "EMBEDDING_API_KEY is not set. This may be required depending on your configuration"
else
    log_info "EMBEDDING_API_KEY is set"
fi

# Step 4: Clone or update the repository
log_step "Processing repository"

# Check if repository directory exists
if [ -d "$REPO_NAME" ]; then
    log_info "Updating existing repository in $REPO_NAME"
    cd "$REPO_NAME"
    git pull
    cd ..
else
    log_info "Cloning repository to $REPO_NAME"
    git clone "$REPO_URL" "$REPO_NAME"
fi

# Step 5: Run the ingestion pipeline
log_step "Running ingestion pipeline"

log_info "Executing pipeline with repository: $REPO_NAME"
# Set environment variable for protobuf implementation to work around compatibility issues
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
log_info "Using pure-Python protobuf implementation for compatibility"

# Build command with appropriate flags
CMD="python main.py \"$REPO_NAME\" --config config.yaml"
if [ "$USE_MOCK" = true ]; then
    CMD="$CMD --mock-mode"
fi
if [ "$USE_FIRECRAWL" = false ]; then
    CMD="$CMD --no-firecrawl"
fi
if [ "$USE_DEEP_RESEARCH" = false ]; then
    CMD="$CMD --no-deep-research"
fi
if [ -n "$SEARCH_QUERY" ]; then
    CMD="$CMD --search-query \"$SEARCH_QUERY\""
fi

# Execute the command
eval $CMD

# Step 6: Report results
log_step "Pipeline execution completed"

log_info "Repository content has been successfully ingested into Pinecone"
log_info "You can now query the index using the Pinecone API or SDK"

# Step 7: Cleanup
log_step "Cleaning up"

# Deactivate virtual environment
log_info "Deactivating virtual environment"
deactivate

log_info "Bootstrap process completed successfully"
echo "============================================================"
