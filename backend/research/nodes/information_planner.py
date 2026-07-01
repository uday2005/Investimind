from backend.research.schemas import InformationPlan
from backend.state import InvestMindState
from backend.llm import llm
from langchain_core.messages import SystemMessage , HumanMessage
from backend.research.prompts.information_planner import INFORMATION_PLANNER_PROMPT

def information_planner_node(state : InvestMindState):
    
    research_brief = state["research_brief"]
    
    structured_llm  = llm.with_structured_output(
        InformationPlan
    )
    
    response = structured_llm.invoke(
        [
            SystemMessage(content=INFORMATION_PLANNER_PROMPT),
            HumanMessage(
                content=f"""
                        Research Brief:
                        {research_brief}
                        """
                        ),
        ]
    )
    # by passing the data to llm like this is research brief it tells specially that input data this is reseach brief
    return {
        "required_information" : response.required_information
    }