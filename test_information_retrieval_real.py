import os

import pytest

from backend.research.nodes.information_retrieval import information_retrieval_node
from backend.tools.normalizers import MAX_CONTENT_CHARS


@pytest.mark.skipif(
    os.getenv("RUN_REAL_TAVILY_TESTS") != "1",
    reason="Set RUN_REAL_TAVILY_TESTS=1 to run live Tavily integration tests.",
)
def test_information_retrieval_real_tavily():
    result = information_retrieval_node(
        {
            "queries": [
                "Nvidia data center revenue 2024 official earnings",
                "Nvidia AI GPU competition AMD MI300X 2024",
            ]
        }
    )

    print("\nNormalized search results:")
    for item in result["search_results"]:
        truncated_marker = " TRUNCATED" if len(item.content) >= MAX_CONTENT_CHARS else ""
        print(f"- query={item.query!r}")
        print(f"  title={item.title!r}")
        print(f"  url={item.url}")
        print(f"  chars={len(item.content)}{truncated_marker}")
        print(f"  preview={item.content[:220]!r}")

    assert result["search_results"]
    assert all(item.url for item in result["search_results"])
    assert all(item.content for item in result["search_results"])
    assert all(len(item.content) <= MAX_CONTENT_CHARS for item in result["search_results"])
