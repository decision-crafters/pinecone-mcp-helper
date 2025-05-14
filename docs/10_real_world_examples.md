# Chapter 10: Real-World Examples

In the previous chapters, we've explored the various components of the Pinecone MCP Helper. Now, let's see how these components come together in real-world scenarios! 🚀

## Example 1: Creating a Technical Documentation Search Engine

### The Challenge

Imagine you're leading a development team with multiple GitHub repositories containing technical documentation. Your team members often struggle to find relevant information across these repositories.

### The Solution

Using Pinecone MCP Helper, you can create a unified search engine for all your technical documentation:

```bash
# Process multiple repositories and combine them in a single index
python main.py https://github.com/your-org/repo1 --config custom_config.yaml
python main.py https://github.com/your-org/repo2 --config custom_config.yaml
python main.py https://github.com/your-org/repo3 --config custom_config.yaml
```

With a custom configuration like:

```yaml
# custom_config.yaml
pinecone:
  dimension: 384
  metric: cosine
  index_name: "technical-documentation"  # Use the same index for all repositories

embedding:
  model: "multilingual-e5-large"

firecrawl:
  max_urls: 30
  deep_research:
    enabled: true
    max_depth: 3
    max_urls: 15

repomix:
  max_files: 200
  excluded_paths:
    - "node_modules/"
    - "__pycache__/"
    - "*.test.js"
    - "*.min.js"
  file_types:
    - ".md"
    - ".rst"
    - ".txt"
    - ".ipynb"
```

### Search Implementation

```python
from repo_ingestion.embedding.embedder import get_embedding_function
from repo_ingestion.pinecone.index_manager import init_pinecone

def search_documentation(query, config, env_vars):
    # Initialize embedding function
    embedding_function = get_embedding_function(config, env_vars)
    
    # Generate query embedding
    query_embedding = embedding_function(query)
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=env_vars["PINECONE_API_KEY"],
        environment=env_vars["PINECONE_ENVIRONMENT"]
    )
    
    # Get index
    index = pinecone_client.Index("technical-documentation")
    
    # Search across all namespaces
    search_results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        namespace="*"  # Search across all namespaces
    )
    
    # Process and return results
    formatted_results = []
    for match in search_results.matches:
        formatted_results.append({
            "score": match.score,
            "repository": match.metadata.get("repository_name", "Unknown"),
            "file_path": match.metadata.get("file_path", "Unknown"),
            "content": match.metadata.get("text", "")[:200] + "...",  # Preview
            "url": match.metadata.get("url", "")
        })
    
    return formatted_results
```

## Example 2: Automated Code Review Assistant

### The Challenge

Your team needs to maintain code quality across multiple repositories, but manual code reviews are time-consuming and sometimes miss important patterns.

### The Solution

Create an automated code review assistant that can analyze repositories and provide insights:

```bash
# Process the repository with deep research enabled
python main.py https://github.com/your-org/target-repo --config code_review_config.yaml --search-query "best practices for secure coding"
```

With a specialized configuration:

```yaml
# code_review_config.yaml
pinecone:
  dimension: 384
  metric: cosine
  index_name: "code-review-assistant"

embedding:
  model: "llama-text-embed-v2"  # Better for code understanding

firecrawl:
  max_urls: 50
  deep_research:
    enabled: true
    max_depth: 4
    max_urls: 20

repomix:
  max_files: 500
  excluded_paths:
    - "node_modules/"
    - "dist/"
    - "build/"
  file_types:
    - ".py"
    - ".js"
    - ".ts"
    - ".java"
    - ".go"
```

### Code Review Implementation

```python
from repo_ingestion.embedding.embedder import get_embedding_function
from repo_ingestion.pinecone.index_manager import init_pinecone
import re

def analyze_code_patterns(repository_name, config, env_vars):
    # Initialize embedding function
    embedding_function = get_embedding_function(config, env_vars)
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=env_vars["PINECONE_API_KEY"],
        environment=env_vars["PINECONE_ENVIRONMENT"]
    )
    
    # Get index
    index = pinecone_client.Index("code-review-assistant")
    
    # Define code patterns to search for
    patterns = [
        "security vulnerability",
        "performance bottleneck",
        "code duplication",
        "error handling",
        "memory leak"
    ]
    
    findings = {}
    
    # Search for each pattern
    for pattern in patterns:
        pattern_embedding = embedding_function(pattern)
        
        search_results = index.query(
            vector=pattern_embedding,
            top_k=10,
            include_metadata=True,
            namespace=get_namespace_for_repo(repository_name)
        )
        
        # Process results
        pattern_findings = []
        for match in search_results.matches:
            if match.score > 0.7:  # Only include high confidence matches
                pattern_findings.append({
                    "file": match.metadata.get("file_path", "Unknown"),
                    "line_number": match.metadata.get("line_number", "Unknown"),
                    "code_snippet": match.metadata.get("text", ""),
                    "confidence": match.score
                })
        
        if pattern_findings:
            findings[pattern] = pattern_findings
    
    return findings
```

## Example 3: Knowledge Base for Machine Learning Projects

### The Challenge

Your organization has multiple machine learning projects, each with its own documentation, code, and research papers. You need a unified knowledge base to help data scientists find relevant information quickly.

### The Solution

Create a comprehensive knowledge base that includes both code repositories and research papers:

```bash
# Process ML repositories
python main.py https://github.com/your-org/ml-project1 --config ml_knowledge_config.yaml
python main.py https://github.com/your-org/ml-project2 --config ml_knowledge_config.yaml

# Add research papers with specific search queries
python main.py https://github.com/your-org/research-papers --config ml_knowledge_config.yaml --search-query "transformer architecture advances" --no-firecrawl
```

With a specialized configuration:

```yaml
# ml_knowledge_config.yaml
pinecone:
  dimension: 384
  metric: cosine
  index_name: "ml-knowledge-base"

embedding:
  model: "multilingual-e5-large"

firecrawl:
  max_urls: 100
  deep_research:
    enabled: true
    max_depth: 5
    max_urls: 30

repomix:
  max_files: 1000
  excluded_paths:
    - "data/"
    - "datasets/"
    - "__pycache__/"
  file_types:
    - ".py"
    - ".ipynb"
    - ".md"
    - ".pdf"
```

### Knowledge Base Query Implementation

```python
from repo_ingestion.embedding.embedder import get_embedding_function
from repo_ingestion.pinecone.index_manager import init_pinecone

def query_ml_knowledge_base(query, config, env_vars, filter_type=None):
    # Initialize embedding function
    embedding_function = get_embedding_function(config, env_vars)
    
    # Generate query embedding
    query_embedding = embedding_function(query)
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=env_vars["PINECONE_API_KEY"],
        environment=env_vars["PINECONE_ENVIRONMENT"]
    )
    
    # Get index
    index = pinecone_client.Index("ml-knowledge-base")
    
    # Prepare filter if needed
    filter_dict = None
    if filter_type:
        filter_dict = {"type": filter_type}  # e.g., "code", "paper", "documentation"
    
    # Search across all namespaces
    search_results = index.query(
        vector=query_embedding,
        top_k=10,
        include_metadata=True,
        filter=filter_dict
    )
    
    # Process and categorize results
    categorized_results = {
        "code_examples": [],
        "research_papers": [],
        "documentation": [],
        "web_content": []
    }
    
    for match in search_results.matches:
        result = {
            "score": match.score,
            "repository": match.metadata.get("repository_name", "Unknown"),
            "title": match.metadata.get("title", "Unknown"),
            "content": match.metadata.get("text", "")[:200] + "...",  # Preview
            "url": match.metadata.get("url", "")
        }
        
        # Categorize based on metadata
        content_type = match.metadata.get("type", "documentation")
        file_path = match.metadata.get("file_path", "")
        
        if content_type == "code" or file_path.endswith((".py", ".ipynb")):
            categorized_results["code_examples"].append(result)
        elif content_type == "paper" or file_path.endswith((".pdf", ".arxiv")):
            categorized_results["research_papers"].append(result)
        elif content_type == "web":
            categorized_results["web_content"].append(result)
        else:
            categorized_results["documentation"].append(result)
    
    return categorized_results
```

## Example 4: Automated API Documentation Generator

### The Challenge

Your team maintains multiple APIs, and keeping the documentation up-to-date is challenging. You need a system that can automatically extract API information from code repositories and generate documentation.

### The Solution

Create an automated API documentation generator:

```bash
# Process API repositories
python main.py https://github.com/your-org/api-service --config api_docs_config.yaml
```

With a specialized configuration:

```yaml
# api_docs_config.yaml
pinecone:
  dimension: 384
  metric: cosine
  index_name: "api-documentation"

embedding:
  model: "multilingual-e5-large"

firecrawl:
  max_urls: 20
  deep_research:
    enabled: true
    max_depth: 2
    max_urls: 10

repomix:
  max_files: 300
  excluded_paths:
    - "node_modules/"
    - "tests/"
    - "examples/"
  file_types:
    - ".py"
    - ".js"
    - ".ts"
    - ".java"
    - ".go"
```

### API Documentation Generator Implementation

```python
from repo_ingestion.embedding.embedder import get_embedding_function
from repo_ingestion.pinecone.index_manager import init_pinecone
import re

def extract_api_endpoints(repository_name, config, env_vars):
    # Initialize embedding function
    embedding_function = get_embedding_function(config, env_vars)
    
    # Initialize Pinecone client
    pinecone_client = init_pinecone(
        api_key=env_vars["PINECONE_API_KEY"],
        environment=env_vars["PINECONE_ENVIRONMENT"]
    )
    
    # Get index
    index = pinecone_client.Index("api-documentation")
    
    # Search for API endpoint patterns
    api_patterns = [
        "API endpoint",
        "route definition",
        "controller method",
        "REST API",
        "GraphQL resolver"
    ]
    
    api_documentation = []
    
    for pattern in api_patterns:
        pattern_embedding = embedding_function(pattern)
        
        search_results = index.query(
            vector=pattern_embedding,
            top_k=50,
            include_metadata=True,
            namespace=get_namespace_for_repo(repository_name)
        )
        
        # Process results to extract API endpoints
        for match in search_results.matches:
            if match.score > 0.6:
                code_snippet = match.metadata.get("text", "")
                file_path = match.metadata.get("file_path", "Unknown")
                
                # Extract API endpoint information using regex patterns
                # (Simplified for example purposes)
                endpoint_info = extract_endpoint_info(code_snippet, file_path)
                
                if endpoint_info:
                    api_documentation.append(endpoint_info)
    
    # Remove duplicates and organize by path
    organized_docs = organize_api_documentation(api_documentation)
    
    return organized_docs

def extract_endpoint_info(code_snippet, file_path):
    # This is a simplified example - in a real implementation,
    # you would use more sophisticated parsing based on the language
    
    # Look for common API patterns
    endpoint_patterns = [
        r'@app\.(?:route|get|post|put|delete)\([\'"]([^\'"]+)[\'"]',  # Flask
        r'app\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]',         # Express
        r'@RequestMapping\([\'"]([^\'"]+)[\'"]',                      # Spring
        r'router\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]'       # Various frameworks
    ]
    
    for pattern in endpoint_patterns:
        matches = re.findall(pattern, code_snippet)
        if matches:
            # Extract method (GET, POST, etc.)
            method = "GET"  # Default
            if "post" in pattern.lower() and "post" in code_snippet.lower():
                method = "POST"
            elif "put" in pattern.lower() and "put" in code_snippet.lower():
                method = "PUT"
            elif "delete" in pattern.lower() and "delete" in code_snippet.lower():
                method = "DELETE"
            
            # Extract description from comments
            description = extract_comment_description(code_snippet)
            
            return {
                "path": matches[0],
                "method": method,
                "description": description,
                "file_path": file_path,
                "code_snippet": code_snippet
            }
    
    return None

def extract_comment_description(code_snippet):
    # Look for docstring or comment blocks
    comment_patterns = [
        r'"""(.*?)"""',          # Python docstring
        r'/\*\*(.*?)\*/',        # JSDoc
        r'///\s*(.*?)(?:\n|$)'   # Single line doc comments
    ]
    
    for pattern in comment_patterns:
        matches = re.findall(pattern, code_snippet, re.DOTALL)
        if matches:
            # Clean up the comment
            description = matches[0].strip()
            description = re.sub(r'\s+', ' ', description)
            return description
    
    return "No description available"

def organize_api_documentation(api_endpoints):
    # Group endpoints by path
    organized = {}
    
    for endpoint in api_endpoints:
        path = endpoint["path"]
        if path not in organized:
            organized[path] = []
        
        # Check if this exact endpoint is already included
        duplicate = False
        for existing in organized[path]:
            if existing["method"] == endpoint["method"]:
                duplicate = True
                break
        
        if not duplicate:
            organized[path].append(endpoint)
    
    return organized
```

## Conclusion

These real-world examples demonstrate the versatility and power of the Pinecone MCP Helper for various use cases:

1. **Technical Documentation Search Engine**: Unify documentation across repositories for easier access
2. **Automated Code Review Assistant**: Identify potential issues and patterns in your codebase
3. **Machine Learning Knowledge Base**: Combine code, documentation, and research papers in a searchable knowledge base
4. **API Documentation Generator**: Automatically extract and organize API information from code

By adapting these examples to your specific needs, you can leverage the full potential of vector embeddings and semantic search to enhance your development workflow and knowledge management.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)
