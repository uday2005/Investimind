from backend.research.schemas import CoverageCheck
from backend.state import InvestMindState
from backend.llm import llm

from langchain_core.messages import SystemMessage, HumanMessage

from backend.research.prompts.coverage_checker import COVERAGE_CHECKER_PROMPT


def coverage_checker_node(state: InvestMindState):

    research_brief = state["research_brief"]
    required_information = state["required_information"]
    research_notes = state["research_notes"]

    structured_llm = llm.with_structured_output(
        CoverageCheck
    )

    response = structured_llm.invoke(
        [
            SystemMessage(
                content=COVERAGE_CHECKER_PROMPT
            ),
            HumanMessage(
                content=f"""
Research Brief:
{research_brief}

Required Information:
{required_information}

Research Notes:
{research_notes}
"""
            ),
        ]
    )

    return {
        "is_sufficient": response.is_sufficient,
        "missing_information": response.missing_information,
        "coverage_assessment": response.coverage_assessment,
        "confidence": response.confidence,
    }