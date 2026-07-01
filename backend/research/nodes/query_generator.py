from backend.research.schemas import SearchQueries
from backend.state import InvestMindState
from backend.llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from backend.research.prompts.query_generator import QUERY_GENERATOR_PROMPT


def query_generator_node(state: InvestMindState):

    required_information: list[str] = state["required_information"]

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
                            """
            ),
        ]
    )

    return {
        "queries": response.queries
    }