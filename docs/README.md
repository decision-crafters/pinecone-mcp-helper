# Pinecone MCP Helper Documentation

This directory contains the documentation for the Pinecone MCP Helper project, which is published to GitHub Pages.

## Documentation Structure

- **Main documentation**: Organized into chapters in the root of the `docs/` directory
- **Architecture Decision Records (ADRs)**: Located in the `adr/` subdirectory
- **Assets**: CSS and other assets are in the `assets/` directory

## Local Development

To run the documentation site locally:

1. Install Ruby and Bundler
2. Run `bundle install` in the `docs/` directory
3. Run `bundle exec jekyll serve`
4. Open your browser to `http://localhost:4000/pinecone-mcp-helper/`

## Contributing to Documentation

1. Create or edit Markdown files in the appropriate directories
2. Follow the existing naming conventions
3. Use Markdown for formatting
4. Mermaid diagrams are supported for visualizations
5. Submit a pull request with your changes

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch. The deployment is handled by a GitHub Action defined in `.github/workflows/deploy-docs.yml`.
