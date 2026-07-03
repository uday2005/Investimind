import os

import pytest

from backend.research.nodes.follow_up_query_generator import (
    follow_up_query_generator_node,
)


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_follow_up_query_generator_real_llm_trace():
    result = follow_up_query_generator_node(
        {
            "missing_information": ["Nvidia AI GPU competition from AMD"],
            "coverage_assessment": (
                "The notes cover Nvidia revenue, but do not include specific "
                "evidence about AMD competition in AI GPUs."
            ),
            "constraints": ["Prioritize official sources and credible benchmarks"],
            "research_iterations": 1,
        }
    )

    print("\nGenerated follow-up queries:")
    for query in result["queries"]:
        print(f"- {query}")
    print(f"research_iterations={result['research_iterations']}")

    assert 1 <= len(result["queries"]) <= 3
    assert result["research_iterations"] == 2
    assert all(query.strip() for query in result["queries"])
