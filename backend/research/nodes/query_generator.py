from backend.research.schemas import SearchQueries
from backend.state import InvestMindState
from backend.llm import query_generator_llm as llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.research.prompts.query_generator import QUERY_GENERATOR_PROMPT
from backend.research.query_budget import MAX_INITIAL_QUERIES, select_unique_queries


def query_generator_node(state: InvestMindState):

    required_information: list[str] = state["required_information"]
    scope: str | None = state.get("scope")
    constraints: list[str] = state.get("constraints", [])

    structured_llm = llm.with_structured_output(
        SearchQueries
    )

    response = structured_llm.invoke(
        [
            SystemMessage(content=QUERY_GENERATOR_PROMPT),
            HumanMessage(
                content=f"""
Information Requirements:
{required_information}

Scope:
{scope}

Constraints:
{constraints}
"""
            ),
        ]
    )

    # One query per requirement gives broad coverage without multiplying every
    # requirement into extra Tavily searches and note-extraction LLM calls.
    query_limit = min(len(required_information), MAX_INITIAL_QUERIES)

    return {
        "queries": select_unique_queries(response.queries, limit=query_limit)
    }
