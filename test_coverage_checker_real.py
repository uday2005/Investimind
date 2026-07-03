import os

import pytest

from backend.research.nodes.coverage_checker import coverage_checker_node
from backend.research.schemas import ResearchNote


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_coverage_checker_real_llm_trace():
    result = coverage_checker_node(
        {
            "objective": "Evaluate Nvidia as a long-term investment.",
            "scope": "Focus on fiscal 2024 and Nvidia's AI/data center business.",
            "constraints": ["Prioritize official earnings reports"],
            "required_information": [
                "Nvidia fiscal 2024 total revenue",
                "Nvidia fiscal 2024 data center revenue",
                "Nvidia AI GPU competition from AMD",
            ],
            "research_notes": [
                ResearchNote(
                    content="For fiscal 2024, Nvidia revenue was $60.9 billion.",
                    source_url="https://investor.nvidia.com/results",
                    query="Nvidia fiscal 2024 revenue official",
                ),
                ResearchNote(
                    content="Fiscal-year Data Center revenue was $47.5 billion.",
                    source_url="https://investor.nvidia.com/results",
                    query="Nvidia fiscal 2024 data center revenue",
                ),
            ],
        }
    )

    print("\nCoverage result:")
    print(f"is_sufficient={result['is_sufficient']}")
    print(f"missing_information={result['missing_information']}")
    print(f"coverage_assessment={result['coverage_assessment']}")

    assert isinstance(result["is_sufficient"], bool)
    assert isinstance(result["missing_information"], list)
    assert result["coverage_assessment"]
