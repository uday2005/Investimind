from backend.state import InvestMindState
from backend.research.query_budget import MAX_TOTAL_QUERIES
MAX_RESEARCH_ITERATIONS = 3

def should_continue(state: InvestMindState):

    iterations = state.get("research_iterations", 0)

    if state["is_sufficient"]:
        return "end"

    if iterations >= MAX_RESEARCH_ITERATIONS:
        return "end"

    # Stop when the paid search budget is exhausted instead of running empty
    # follow-up rounds that would still spend coverage-checker LLM tokens.
    if len(set(state.get("searched_queries", []))) >= MAX_TOTAL_QUERIES:
        return "end"

    return "continue"
