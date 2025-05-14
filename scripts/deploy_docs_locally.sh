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

# Install compatible bundler version
echo "📦 Installing compatible Bundler..."
gem install bundler -v 2.4.22 --user-install

# Add gem bin directory to PATH
GEM_BIN_DIR=$(ruby -e 'puts Gem.user_dir')/bin
export PATH="$GEM_BIN_DIR:$PATH"
echo "🔄 Added $GEM_BIN_DIR to PATH"

# Navigate to docs directory
cd docs

# Update Gemfile to use compatible Jekyll version if needed
if grep -q "github-pages" Gemfile; then
    echo "⚙️ Updating Gemfile for compatibility..."
    # Create a backup of the original Gemfile
    cp Gemfile Gemfile.bak
    
    # Replace github-pages with Jekyll
    sed -i '' 's/gem "github-pages"/gem "jekyll", "~> 3.9.3"/' Gemfile
    
    # Add required gems if they don't exist
    if ! grep -q "webrick" Gemfile; then
        echo 'gem "webrick", "~> 1.8"' >> Gemfile
    fi
    
    if ! grep -q "kramdown-parser-gfm" Gemfile; then
        echo 'gem "kramdown-parser-gfm"' >> Gemfile
    fi
fi

# Install dependencies locally (no sudo required)
echo "📦 Installing dependencies locally..."
bundle _2.4.22_ config set --local path "$VENDOR_DIR"
bundle _2.4.22_ config set --local without 'production'
bundle _2.4.22_ install

# Build the site
echo "🔨 Building the documentation site..."
bundle _2.4.22_ exec jekyll build --destination ../docs-site

# Serve the site
echo "🌐 Starting local server..."
echo "📝 Documentation will be available at http://localhost:4000"
echo "🛑 Press Ctrl+C to stop the server"
bundle _2.4.22_ exec jekyll serve --destination ../docs-site --host 0.0.0.0

# This part will only execute if the server is stopped
echo "✅ Local server stopped"
