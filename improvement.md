## Research Agent — Future Improvements

### Tool Selector Node
Currently information_retrieval_node calls Tavily directly.
Future: Add a Tool Selector node that decides which tools to call
based on query type (web search, financial data, SEC filings).

### Normalizer
Each tool needs its own normalizer to convert raw output 
to SearchResult schema before Note Extractor reads it.
Priority order: Tavily (done) → Yahoo Finance → SEC → MCP