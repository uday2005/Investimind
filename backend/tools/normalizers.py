from dataclasses import dataclass

import re

MAX_CONTENT_CHARS = 1500
# How do we optimized is question now it can be like missing some important information also

def clean_content(text: str) -> str:
    text = re.sub(r'#+ ', '', text)      # remove markdown headers
    text = re.sub(r'\*+', '', text)      # remove bold/italic markers
    text = re.sub(r'\s+', ' ', text)     # collapse whitespace
    return text.strip()[:MAX_CONTENT_CHARS]

@dataclass
class SearchResult:
    query: str
    title: str
    url: str
    content: str
    source: str = "tavily"

def normalize_tavily(raw: dict) -> list[SearchResult]:
    query = raw.get("query", "")
    results = raw.get("results", [])

    normalized = []
    seen_urls = set()

    for result in results:
        url = result.get("url", "")
        content = clean_content(result.get("content", ""))

        if not url or not content or url in seen_urls:
            continue

        seen_urls.add(url)
        normalized.append(
            SearchResult(
                query=query,
                title=result.get("title", ""),
                url=url,
                content=content,
                source="tavily",
            )
        )

    return normalized
