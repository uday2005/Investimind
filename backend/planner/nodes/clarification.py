from backend.state import InvestMindState
from langchain_core.messages import AIMessage, SystemMessage
from backend.planner.schemas import ClarifyWithUser
from backend.planner.prompts.clarification import CLARIFICATION_SYSTEM_PROMPT
from backend.llm import clarification_llm as llm


DEFAULT_CLARIFICATION_QUESTION = (
    "What specific question or decision would you like this research to address?"
)

# Hard cap, in the same spirit as your query/note budgets.
# 1 = ask at most once, then proceed. Set to 0 to never ask.
MAX_CLARIFICATION_ROUNDS = 1


def clarification_node(state: InvestMindState):
    messages = state["messages"]

    # Assistant turns in this history are only ever clarification questions,
    # so the AIMessage count equals how many rounds we've already asked.
    prior_rounds = sum(1 for m in messages if isinstance(m, AIMessage))
    if prior_rounds >= MAX_CLARIFICATION_ROUNDS:
        # Budget spent — stop asking and let research proceed with what we have.
        return {"need_clarification": False, "clarification_question": None}

    structured_llm = llm.with_structured_output(ClarifyWithUser)
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