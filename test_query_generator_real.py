import os

import pytest

from backend.research.nodes.query_generator import query_generator_node


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_query_generator_real_llm_trace():
    result = query_generator_node(
        {
            "required_information": [
                "Nvidia data center revenue by year",
                "Nvidia AI GPU competitive position versus AMD",
            ],
            "scope": "Last 3 years, Nvidia data center and AI accelerator business",
            "constraints": ["Prioritize official earnings reports"],
        }
    )

    print("\nGenerated queries:")
    for query in result["queries"]:
        print(f"- {query}")

    assert 1 <= len(result["queries"]) <= 8
    assert all(isinstance(query, str) and query.strip() for query in result["queries"])
