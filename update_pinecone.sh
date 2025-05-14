#!/bin/bash

# Color codes for output formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
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

# Activate the test virtual environment
log_info "Activating test virtual environment"
source "test_venv/bin/activate"

# Update the Pinecone SDK to the latest version
log_info "Updating Pinecone SDK to the latest version"
pip install --upgrade pinecone-client

# Deactivate the virtual environment
log_info "Deactivating virtual environment"
deactivate

log_info "Pinecone SDK update completed"
