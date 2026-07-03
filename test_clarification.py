import pytest
from langchain_core.messages import HumanMessage

from backend.planner.graph import planner_graph


def run_planner(user_message: str) -> dict:
    return planner_graph.invoke(
        {
            "messages": [HumanMessage(content=user_message)]
        }
    )


@pytest.mark.parametrize(
    ("user_message", "expected_need_clarification"),
    [
        ("Tell me about Apple.", True),
        ("Compare Tesla.", True),
        ("Research AI.", True),
        ("Analyze Nvidia as a long-term investment.", False),
        ("Compare PostgreSQL and MongoDB for a SaaS backend.", False),
    ],
)
def test_clarification_decision(user_message, expected_need_clarification):
    result = run_planner(user_message)

    assert result["need_clarification"] is expected_need_clarification

    if expected_need_clarification:
        assert result["clarification_question"]
        assert result["clarification_question"].count("?") <= 1
        assert result.get("objective") in (None, "")
    else:
        assert result["clarification_question"] is None
