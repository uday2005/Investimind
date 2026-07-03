import pytest
from langchain_core.messages import HumanMessage

from backend.planner.nodes.research_brief import research_brief_node


def run_research_brief(user_message: str) -> dict:
    return research_brief_node(
        {
            "messages": [HumanMessage(content=user_message)]
        }
    )


@pytest.mark.parametrize(
    ("user_message", "expected_terms"),
    [
        (
            "Analyze Nvidia as a long-term investment.",
            ["nvidia", "investment"],
        ),
        (
            "Compare Nvidia and AMD AI accelerators over the last 3 years.",
            ["nvidia", "amd", "accelerators"],
        ),
        (
            "Analyze India's EV market growth and charging infrastructure.",
            ["india", "ev", "charging"],
        ),
        (
            "Explain Retrieval-Augmented Generation for enterprise search.",
            ["retrieval", "generation", "enterprise"],
        ),
        (
            "Compare Rust and Go for building backend APIs.",
            ["rust", "go", "backend"],
        ),
    ],
)
def test_research_brief_fields(user_message, expected_terms):
    result = run_research_brief(user_message)

    assert result["objective"]
    assert result["scope"]
    assert isinstance(result["constraints"], list)
    assert isinstance(result["required_information"], list)
    assert len(result["constraints"]) <= 5
    assert 1 <= len(result["required_information"]) <= 8

    combined_brief = " ".join(
        [
            result["objective"],
            result["scope"],
            " ".join(result["constraints"]),
            " ".join(result["required_information"]),
        ]
    ).lower()

    for term in expected_terms:
        assert term in combined_brief
