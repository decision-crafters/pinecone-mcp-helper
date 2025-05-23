# Use Firecrawl SDK Instead of MCP Functions

## Status
Accepted

## Context
The project initially used Model Context Protocol (MCP) functions to interact with the Firecrawl API. However, this approach had several limitations:
- Limited functionality compared to the official SDK
- Inconsistent response handling
- Lack of proper error handling and debugging capabilities
- Difficulty in maintaining and updating as the Firecrawl API evolves

The team needed a more reliable and maintainable way to integrate with Firecrawl to ensure that web content could be properly searched, scraped, and stored in the Pinecone vector database.

## Domain Model

The following diagram illustrates the domain model for the Firecrawl integration, showing the key concepts and their relationships:

```mermaid
classDiagram
    class FirecrawlClient {
        -api_key: string
        -client: FirecrawlSDK
        +search(query, limit, scrapeOptions)
        +scrape(url, formats, onlyMainContent, waitFor)
        +deep_research(query, maxDepth, maxUrls, timeLimit)
    }
    
    class SearchResult {
        +url: string
        +title: string
        +description: string
        +content: string
        +source_type: string
    }
    
    class ScrapeResult {
        +url: string
        +title: string
        +content: string
        +formats: List[string]
        +metadata: Map<string, any>
    }
    
    class DeepResearchResult {
        +query: string
        +summary: string
        +sources: List[Source]
        +insights: List[string]
    }
    
    class Source {
        +url: string
        +title: string
        +relevance: float
        +content_snippet: string
    }
    
    class WebContentProcessor {
        +process_search_results(results)
        +process_scrape_result(result)
        +extract_metadata(content)
    }
    
    FirecrawlClient ..> SearchResult: produces
    FirecrawlClient ..> ScrapeResult: produces
    FirecrawlClient ..> DeepResearchResult: produces
    DeepResearchResult *-- Source: contains
    WebContentProcessor ..> SearchResult: processes
    WebContentProcessor ..> ScrapeResult: processes
```

This domain model establishes clear boundaries between the client interface, the different types of results, and the processing components. It defines a consistent vocabulary for discussing web content retrieval and processing across the codebase.

## Decision
We decided to replace the MCP functions with the official Firecrawl Python SDK (version 2.5.4). This involved:
- Updating the FirecrawlClient class to use the SDK
- Enhancing error handling and logging
- Fixing response handling in search and scrape methods
- Adding validation tools to ensure proper integration

The implementation follows our team's "Understand the System" principle by ensuring a comprehensive understanding of the Firecrawl API and SDK before making changes. We also adhered to the "Change One Thing at a Time" principle by focusing solely on the Firecrawl integration without modifying other components.

## Consequences
### Positive
- More reliable and consistent interaction with the Firecrawl API
- Better error handling and debugging capabilities
- Access to the full range of Firecrawl features
- Easier maintenance and updates as the SDK evolves
- Improved code readability and maintainability
- Real web content is now successfully retrieved and stored in the Pinecone index

### Negative
- Required changes to existing code and interfaces
- Added a new dependency to the project
- May require updates if the SDK API changes in the future

## Alternatives Considered
1. **Improve the existing MCP functions**: We could have enhanced the existing MCP functions with better error handling and response processing. However, this would still limit us to the functionality exposed by the MCP interface and would require ongoing maintenance to keep up with API changes.

2. **Create a custom client**: We could have developed a custom client for the Firecrawl API without using the SDK. This would give us full control over the implementation but would require significant development effort and ongoing maintenance.

3. **Use a different web scraping/search solution**: We considered alternative solutions for web scraping and search but determined that Firecrawl's capabilities best met our requirements for integration with the Pinecone vector database.
