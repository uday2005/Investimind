from backend.state import InvestMindState
from backend.llm import llm
from backend.planner.schemas import ResearchBrief
from backend.planner.prompts.research_brief import RESEARCH_BRIEF_PROMPT
from langchain_core.messages import SystemMessage

def research_brief_node(state : InvestMindState):
    
    messages = state["messages"]
    
    structured_llm = llm.with_structured_output(
        ResearchBrief,
    )

    response = structured_llm.invoke(
        [
        SystemMessage(RESEARCH_BRIEF_PROMPT),
        *messages #we are unpacking all the messages in history as otherwise it woudl have become the lsit of list which we don't want
        ]
    )
    
    # return response
    return {
    "objective": response.objective,
    "scope": response.scope,
    "constraints": response.constraints,
    "required_information": response.required_information
}