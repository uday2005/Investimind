
from backend.state import InvestMindState
from langchain_core.messages import SystemMessage
from backend.planner.schemas import ClarifyWithUser
from backend.planner.prompts.clarification import CLARIFICATION_SYSTEM_PROMPT
from backend.llm import llm

system_prompt = SystemMessage(
    content=CLARIFICATION_SYSTEM_PROMPT
)

def clarification_node(state: InvestMindState):
    """
    Determines whether the user's request contains enough
    information to begin research.

    If more information is required, returns a clarification
    question for the user.
    """
    
    messages = state["messages"]
    
    # we like a put a wrapper around llm so it give ouypt like our schemas
    structured_llm = llm.with_structured_output(
        ClarifyWithUser
    )
    
    response = structured_llm.invoke(
        [
            SystemMessage(content = CLARIFICATION_SYSTEM_PROMPT),
            *messages
        ]
    )
    
    # return response
    return {
    "need_clarification": response.need_clarification
    }
    
    
    
    