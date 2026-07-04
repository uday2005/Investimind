from langgraph.graph import END, START, StateGraph

from backend.planner.graph import planner_graph
from backend.research.graph import research_graph
from backend.state import InvestMindState
from backend.writer.graph import writer_graph


def should_run_research(state: InvestMindState):
    if state.get("need_clarification"):
        return "clarify"

    return "research"


def build_investmind_graph(
    planner=planner_graph,
    research=research_graph,
    writer=writer_graph,
):
    builder = StateGraph(InvestMindState)

    builder.add_node("planner", planner)
    builder.add_node("research", research)
    builder.add_node("writer", writer)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        should_run_research,
        {
            "clarify": END,
            "research": "research",
        },
    )
    builder.add_edge("research", "writer")
    builder.add_edge("writer", END)

    return builder.compile()


investmind_graph = build_investmind_graph()
