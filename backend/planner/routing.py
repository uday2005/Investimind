from backend.state import InvestMindState


def should_generate_research_brief(state: InvestMindState):

    if state["need_clarification"]:
        return "clarify"

    return "research_brief"