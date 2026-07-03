import backend.research.nodes.information_retrieval as retrieval_module
from backend.tools.normalizers import MAX_CONTENT_CHARS, normalize_tavily


def test_normalize_tavily_cleans_dedupes_and_limits_content():
    raw = {
        "query": "Nvidia data center revenue",
        "results": [
            {
                "title": "First",
                "url": "https://example.com/first",
                "content": "## Heading\n**Revenue**   grew   quickly.",
            },
            {
                "title": "Duplicate",
                "url": "https://example.com/first",
                "content": "Duplicate should be skipped.",
            },
            {
                "title": "No content",
                "url": "https://example.com/empty",
                "content": "",
            },
            {
                "title": "Long",
                "url": "https://example.com/long",
                "content": "x" * (MAX_CONTENT_CHARS + 100),
            },
        ],
    }

    results = normalize_tavily(raw)

    assert len(results) == 2
    assert results[0].query == "Nvidia data center revenue"
    assert results[0].title == "First"
    assert results[0].url == "https://example.com/first"
    assert results[0].source == "tavily"
    assert results[0].content == "Heading Revenue grew quickly."
    assert len(results[1].content) == MAX_CONTENT_CHARS


def test_information_retrieval_node_calls_tavily_for_each_query(monkeypatch):
    calls = []

    def fake_tavily_search(query):
        calls.append(query)
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result for {query}",
                    "url": f"https://example.com/{query.replace(' ', '-')}",
                    "content": f"Content for {query}",
                }
            ],
        }

    monkeypatch.setattr(retrieval_module, "tavily_search", fake_tavily_search)

    result = retrieval_module.information_retrieval_node(
        {
            "queries": [
                "Nvidia data center revenue",
                "Nvidia AI GPU competition AMD",
            ]
        }
    )

    assert calls == [
        "Nvidia data center revenue",
        "Nvidia AI GPU competition AMD",
    ]
    assert len(result["search_results"]) == 2
    assert result["search_results"][0].query == "Nvidia data center revenue"
    assert result["search_results"][1].query == "Nvidia AI GPU competition AMD"


def test_information_retrieval_skips_duplicates_and_enforces_total_budget(monkeypatch):
    calls = []

    def fake_tavily_search(query):
        calls.append(query)
        return {"query": query, "results": []}

    monkeypatch.setattr(retrieval_module, "tavily_search", fake_tavily_search)

    result = retrieval_module.information_retrieval_node(
        {
            "queries": ["past query 0", "new query", "another query"],
            "searched_queries": [f"past query {index}" for index in range(9)],
        }
    )

    assert calls == ["new query"]
    assert result["queries"] == ["new query"]
    assert result["searched_queries"] == ["new query"]
