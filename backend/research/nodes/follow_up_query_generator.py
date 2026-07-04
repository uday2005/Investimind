from backend.research.schemas import SearchQueries
from backend.state import InvestMindState
from backend.llm import follow_up_query_generator_llm as llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.research.prompts.query_generator import FOLLOW_UP_QUERY_GENERATOR_PROMPT
from backend.research.query_budget import (
    MAX_FOLLOW_UP_QUERIES,
    MAX_TOTAL_QUERIES,
    select_unique_queries,
)


def follow_up_query_generator_node(state: InvestMindState):

    missing_information: list[str] = state["missing_information"]
    coverage_assessment: str | None = state.get("coverage_assessment")
    constraints: list[str] = state.get("constraints", [])
    searched_queries: list[str] = state.get("searched_queries", [])
    remaining_budget = max(0, MAX_TOTAL_QUERIES - len(set(searched_queries)))

    # Avoid paying for a follow-up generation when no Tavily calls remain.
    if remaining_budget == 0:
        return {
            "queries": [],
            "research_iterations": state.get("research_iterations", 0) + 1,
        }

    structured_llm = llm.with_structured_output(
        SearchQueries
    )

    response = structured_llm.invoke(
        [
            SystemMessage(content=FOLLOW_UP_QUERY_GENERATOR_PROMPT),
            HumanMessage(
                content=f"""
Coverage Assessment:
{coverage_assessment}

Missing Information:
{missing_information}

Constraints:
{constraints}
"""
            ),
        ]
    )

    # Follow-ups only use the remaining global search budget and never repeat a
    # query that Tavily has already received in an earlier research round.
    query_limit = min(MAX_FOLLOW_UP_QUERIES, remaining_budget)
    queries = select_unique_queries(
        response.queries,
        limit=query_limit,
        excluded=searched_queries,
    )

    return {
        "queries": queries,
        "research_iterations": state.get("research_iterations", 0) + 1,
    }
