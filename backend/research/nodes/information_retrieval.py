from backend.tools.tavily import tavily_search
from backend.state import InvestMindState
def information_retrieval_node(state: InvestMindState):

    queries = state["queries"]

    search_results = []

    for query in queries:

        search_results.append(
            tavily_search(query)
        )

    return {
        "search_results": search_results
    }