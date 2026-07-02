from backend.state import InvestMindState
MAX_RESEARCH_ITERATIONS = 3

def should_continue(state: InvestMindState):

    iterations = state.get("research_iterations", 0)

    if state["is_sufficient"]:
        return "end"

    if iterations >= MAX_RESEARCH_ITERATIONS:
        return "end"

    return "follow_up_query_generator"