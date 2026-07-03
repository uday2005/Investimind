from langchain_core.messages import HumanMessage

from backend.graph import build_investmind_graph, should_run_research


def test_should_run_research_routes_clarification_to_end():
    assert should_run_research({"need_clarification": True}) == "clarify"


def test_should_run_research_routes_clear_request_to_research():
    assert should_run_research({"need_clarification": False}) == "research"


def test_investmind_graph_stops_when_planner_needs_clarification():
    def fake_planner(_state):
        return {
            "need_clarification": True,
            "clarification_question": "Which Apple do you mean: Apple Inc. or the fruit?",
        }

    def fake_research(_state):
        raise AssertionError("Research should not run when clarification is needed.")

    graph = build_investmind_graph(
        planner=fake_planner,
        research=fake_research,
    )

    result = graph.invoke(
        {"messages": [HumanMessage(content="Tell me about Apple.")]}
    )

    assert result["need_clarification"] is True
    assert "Which Apple" in result["clarification_question"]
    assert "queries" not in result


def test_investmind_graph_runs_research_after_clear_planner_output():
    def fake_planner(_state):
        return {
            "need_clarification": False,
            "objective": "Compare Nvidia and AMD AI accelerators.",
            "scope": "Last 3 years, global data center market.",
            "constraints": ["Prioritize official sources"],
            "required_information": [
                "Nvidia AI accelerator revenue",
                "AMD AI accelerator revenue",
            ],
        }

    def fake_research(state):
        assert state["objective"] == "Compare Nvidia and AMD AI accelerators."
        assert state["required_information"] == [
            "Nvidia AI accelerator revenue",
            "AMD AI accelerator revenue",
        ]
        return {
            "queries": [
                "Nvidia AI accelerator revenue last 3 years",
                "AMD AI accelerator revenue last 3 years",
            ],
            "is_sufficient": True,
            "missing_information": [],
        }

    graph = build_investmind_graph(
        planner=fake_planner,
        research=fake_research,
    )

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Compare Nvidia and AMD AI accelerators over the last 3 years."
                )
            ]
        }
    )

    assert result["need_clarification"] is False
    assert result["queries"] == [
        "Nvidia AI accelerator revenue last 3 years",
        "AMD AI accelerator revenue last 3 years",
    ]
    assert result["is_sufficient"] is True
