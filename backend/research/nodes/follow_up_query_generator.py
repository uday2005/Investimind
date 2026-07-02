from backend.research.schemas import SearchQueries
from backend.state import InvestMindState
from backend.llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.research.prompts.query_generator import FOLLOW_UP_QUERY_GENERATOR_PROMPT


def follow_up_query_generator_node(state: InvestMindState):

    missing_information: list[str] = state["required_information"]
    coverage_assessment : list[str] = state["covergae_assesment"]

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
    """
            ),
        ]
    )

    return {
        "queries": response.queries,
        "research_iterations": state["research_iterations"] + 1,
    }