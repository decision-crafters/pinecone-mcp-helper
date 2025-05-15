#!/bin/bash

# Script to build and serve the documentation site locally
# Created: 2025-05-14

set -e  # Exit on error

echo "🚀 Starting local documentation deployment..."

# Navigate to the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check if Ruby is installed
if ! command -v ruby &> /dev/null; then
    echo "❌ Ruby is not installed. Please install Ruby first."
    exit 1
fi

# Get Ruby version
RUBY_VERSION=$(ruby -e 'puts RUBY_VERSION')
echo "📊 Detected Ruby version: $RUBY_VERSION"

# Create a vendor directory for local gem installation
VENDOR_DIR="$PROJECT_ROOT/vendor/bundle"
mkdir -p "$VENDOR_DIR"

# Navigate to the docs directory
cd "$PROJECT_ROOT/docs"

# Create a simple _sass directory with just-the-docs import if it doesn't exist
if [ ! -d "_sass" ]; then
    echo "📚 Creating _sass directory for theme imports..."
    mkdir -p "_sass"
    echo "// Just the Docs theme placeholder" > "_sass/just-the-docs.scss"
fi

# Install dependencies using system bundler
echo "📦 Installing dependencies..."
bundle config set --local path "$VENDOR_DIR"
bundle install

# Build and serve the site
echo "🔨 Building and serving the documentation site..."
echo "📝 Documentation will be available at http://localhost:4000"
echo "🛑 Press Ctrl+C to stop the server"
bundle exec jekyll serve --livereload --baseurl '' --trace

# This part will only execute if the server is stopped
echo "✅ Local server stopped"
