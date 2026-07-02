from langgraph.graph import StateGraph, START, END

from backend.state import InvestMindState

from backend.planner.nodes.clarification import clarification_node
from backend.planner.nodes.research_brief import research_brief_node

from backend.planner.routing import should_generate_research_brief


builder = StateGraph(InvestMindState)

# ----------------------------------------------------------
# Nodes
# ----------------------------------------------------------

builder.add_node(
    "clarification",
    clarification_node,
)

builder.add_node(
    "research_brief",
    research_brief_node,
)

# ----------------------------------------------------------
# Flow
# ----------------------------------------------------------

builder.add_edge(
    START,
    "clarification",
)

builder.add_conditional_edges(
    "clarification",
    should_generate_research_brief,
    {
        "clarify": END,
        "research_brief": "research_brief",
    },
)

builder.add_edge(
    "research_brief",
    END,
)

planner_graph = builder.compile()