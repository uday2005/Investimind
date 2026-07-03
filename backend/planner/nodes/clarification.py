
from backend.state import InvestMindState
from langchain_core.messages import SystemMessage
from backend.planner.schemas import ClarifyWithUser
from backend.planner.prompts.clarification import CLARIFICATION_SYSTEM_PROMPT
from backend.llm import llm


DEFAULT_CLARIFICATION_QUESTION = (
    "What specific question or decision would you like this research to address?"
)


def clarification_node(state: InvestMindState):
    """
    Determines whether the user's request contains enough
    information to begin research.

    If more information is required, returns a clarification
    question for the user.
    """
    messages = state["messages"]

    structured_llm = llm.with_structured_output(
        ClarifyWithUser,
    )

    response = structured_llm.invoke(
        [
            SystemMessage(content=CLARIFICATION_SYSTEM_PROMPT),
            *messages,
        ]
    )

    if response.need_clarification:
        clarification_question = (
            response.clarification_question or ""
        ).strip() or DEFAULT_CLARIFICATION_QUESTION
    else:
        clarification_question = None

    return {
        "need_clarification": response.need_clarification,
        "clarification_question": clarification_question,
    }
