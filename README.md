# Git Repository to Pinecone Ingestion Pipeline

This Python script automates the process of ingesting content from a Git repository and associated web links into a Pinecone vector database. The script clones a specified repository, processes its content using Repomix, identifies external links, scrapes/searches those links using Firecrawl, embeds all collected text content into vectors, and finally upserts these vectors into a structured Pinecone index.

## Features

- Clone or update Git repositories
- Process repository content using Repomix
- Extract URLs from repository content
- Scrape web content using Firecrawl
- Generate vector embeddings for text content
- Upsert vectors to Pinecone with appropriate metadata
- Comprehensive error handling and logging

> ⚠️ **Note:** Firecrawl search and deep research features are still in testing and may not work as expected. Results may vary depending on your environment and API access.

## Requirements

- Python 3.8+
- Git
- Repomix
- Pinecone API key
- Firecrawl API key
- Embedding API key (optional, depending on the embedding model)

## Project Structure

```
.
├── config.yaml                # Configuration file
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── repo_ingestion/            # Main package
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface
│   ├── pipeline.py            # Pipeline integration
│   ├── config/                # Configuration handling
│   │   ├── __init__.py
│   │   └── config_loader.py
│   ├── embedding/             # Embedding functionality
│   │   ├── __init__.py
│   │   └── embedder.py
│   ├── firecrawl/             # Firecrawl integration
│   │   ├── __init__.py
│   │   └── crawler.py
│   ├── git/                   # Git repository management
│   │   ├── __init__.py
│   │   └── repo_manager.py
│   ├── pinecone/              # Pinecone integration
│   │   ├── __init__.py
│   │   └── index_manager.py
│   ├── repomix/               # Repomix processing
│   │   ├── __init__.py
│   │   └── processor.py
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       └── logging_utils.py
└── tests/                     # Unit tests
    ├── __init__.py
    ├── test_config_loader.py
    ├── test_firecrawl_crawler.py
    ├── test_repo_manager.py
    └── test_repomix_processor.py
```

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the required environment variables:
   ```bash
   export PINECONE_API_KEY=your_pinecone_api_key
   export PINECONE_ENVIRONMENT=your_pinecone_environment
   export FIRECRAWL_API_KEY=your_firecrawl_api_key
   export EMBEDDING_API_KEY=your_embedding_api_key  # Optional, depending on the embedding model
   ```

   Alternatively, you can create a `.env` file in the project root with these variables:
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   EMBEDDING_API_KEY=your_embedding_api_key
   ```

## Configuration

The script uses a YAML configuration file (`config.yaml`) to specify parameters for the pipeline. Here's an example configuration:

```yaml
pinecone:
  dimension: 1536  # Vector dimension for the Pinecone index
  metric: cosine   # Similarity metric (cosine, dotproduct, euclidean)

embedding:
  model: multilingual-e5-large  # Embedding model to use
```

### Configuration Options

#### Pinecone Configuration

- `pinecone.dimension`: Integer specifying the vector dimension for the Pinecone index (e.g., 1536)
- `pinecone.metric`: String specifying the similarity metric for the Pinecone index (e.g., `cosine`, `dotproduct`, `euclidean`)

#### Embedding Configuration

- `embedding.model`: String specifying the identifier or name of the embedding model to use. Supported models:
  - `multilingual-e5-large`: Multilingual dense embedding model
  - `llama-text-embed-v2`: High-performance dense embedding model
  - `pinecone-sparse-english-v0`: Sparse embedding model for keyword or hybrid search

## Usage

Run the script with a Git repository URL or local path:

```bash
python main.py https://github.com/user/repo.git
```

### Command-line Options

```bash
python main.py --help
```

Available options:

- `repo_url`: URL of the Git repository to ingest or path to a local Git repository (required positional argument)
- `--config`: Path to the YAML configuration file (default: `config.yaml`)
- `--log-level`: Set the logging level (choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, default: `INFO`)
- `--log-file`: Path to the log file (if not provided, logs will only be written to the console)

## Pipeline Architecture

The script follows a sequential pipeline architecture:

1. **Initialization & Input:** Receive the Git repository URL and load configuration.
2. **Repository Management:** Clone or update the target repository.
3. **Repomix Processing:** Run Repomix on the local repository and capture its output.
4. **Repomix Output Parsing & Chunking:** Read, parse, and chunk the Repomix output.
5. **Embedding Preparation:** Configure the embedding model based on settings.
6. **Pinecone Index Management:** Ensure the target Pinecone index exists (create if necessary).
7. **Repomix Data Embedding & Ingestion:** Embed Repomix chunks and upsert to Pinecone.
8. **Firecrawl URL Identification:** Extract URLs from the Repomix output.
9. **Firecrawl Processing:** Use Firecrawl SDK to scrape/search extracted URLs.
10. **Firecrawl Data Embedding & Ingestion:** Chunk and embed Firecrawl results and upsert to the same Pinecone index.
11. **Completion/Reporting:** Indicate success or failure.

## Data Flow

1. **Repository Content**: Processed by Repomix and stored in an XML file
2. **Content Chunks**: Extracted from the XML file with metadata (file path, source type)
3. **Embeddings**: Generated for each content chunk using the configured embedding model
4. **Vectors**: Upserted to Pinecone with metadata for traceability
5. **URLs**: Extracted from repository content and processed by Firecrawl
6. **Web Content**: Scraped from URLs, chunked, embedded, and upserted to Pinecone

## Error Handling

The script implements robust error handling for various stages of the pipeline:

- CLI argument parsing
- Configuration loading
- Environment variable validation
- Git operations
- Repomix execution and output parsing
- Embedding
- Pinecone API calls
- Firecrawl API calls
- File system operations

## Testing

The project includes comprehensive unit tests for all components. To run the tests:

```bash
python -m pytest
```

To run tests with verbose output:

```bash
python -m pytest -v
```

To run a specific test file:

```bash
python -m pytest tests/test_config_loader.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

[MIT License](LICENSE)
