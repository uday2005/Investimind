from langgraph.graph import StateGraph, START, END

from backend.state import InvestMindState

from backend.research.nodes.query_generator import query_generator_node
from backend.research.nodes.information_retrieval import information_retrieval_node
from backend.research.nodes.note_extractor import note_extractor_node
from backend.research.nodes.coverage_checker import coverage_checker_node
from backend.research.nodes.follow_up_query_generator import (
    follow_up_query_generator_node,
)

from backend.research.routing import should_continue


builder = StateGraph(InvestMindState)

# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------

builder.add_node("query_generator", query_generator_node)
builder.add_node("information_retrieval", information_retrieval_node)
builder.add_node("note_extractor", note_extractor_node)
builder.add_node("coverage_checker", coverage_checker_node)
builder.add_node("follow_up_query_generator", follow_up_query_generator_node)

# ------------------------------------------------------------------
# Initial Flow
# ------------------------------------------------------------------

builder.add_edge(START, "query_generator")
builder.add_edge("query_generator", "information_retrieval")
builder.add_edge("information_retrieval", "note_extractor")
builder.add_edge("note_extractor", "coverage_checker")

# ------------------------------------------------------------------
# Research Loop
# ------------------------------------------------------------------

builder.add_conditional_edges(
    "coverage_checker",
    should_continue,
    {
        "continue": "follow_up_query_generator",
        "end": END,
    },
)

builder.add_edge("follow_up_query_generator", "information_retrieval")

research_graph = builder.compile()