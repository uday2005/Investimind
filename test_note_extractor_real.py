import os

import pytest

from backend.research.nodes.note_extractor import note_extractor_node
from backend.tools.normalizers import SearchResult


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_note_extractor_real_llm_trace():
    result = note_extractor_node(
        {
            "required_information": [
                "Nvidia fiscal 2024 data center revenue",
                "Nvidia fiscal 2024 total revenue",
            ],
            "search_results": [
                SearchResult(
                    query="Nvidia fiscal 2024 data center revenue official earnings",
                    title="NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2024",
                    url="https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2024",
                    content=(
                        "NVIDIA today reported revenue for the fourth quarter ended "
                        "January 28, 2024, of $22.1 billion, up 22% from the previous "
                        "quarter and up 265% from a year ago. For fiscal 2024, revenue "
                        "was $60.9 billion, up 126%. Data Center revenue for the fourth "
                        "quarter was $18.4 billion, up 27% from the previous quarter "
                        "and up 409% from a year ago. Fiscal-year Data Center revenue "
                        "was $47.5 billion, up 217%."
                    ),
                )
            ],
        }
    )

    print("\nExtracted notes:")
    for note in result["research_notes"]:
        print(f"- {note.content}")
        print(f"  source={note.source_url}")
        print(f"  query={note.query}")

    assert result["research_notes"]
    assert len(result["research_notes"]) <= 5
    assert all(note.source_url for note in result["research_notes"])
    assert all(note.query for note in result["research_notes"])
