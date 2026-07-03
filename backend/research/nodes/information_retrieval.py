from backend.tools.tavily import tavily_search
from backend.tools.normalizers import normalize_tavily
from backend.state import InvestMindState
from backend.research.query_budget import MAX_TOTAL_QUERIES, select_unique_queries

def information_retrieval_node(state: InvestMindState):
    queries = state["queries"]
    searched_queries = state.get("searched_queries", [])
    search_results = []

    # This is the final deterministic guard before paid Tavily calls, even if a
    # model or another caller supplies too many or duplicate queries.
    remaining_budget = max(0, MAX_TOTAL_QUERIES - len(set(searched_queries)))
    selected_queries = select_unique_queries(
        queries,
        limit=remaining_budget,
        excluded=searched_queries,
    )

    for query in selected_queries:
        raw = tavily_search(query)
        normalized = normalize_tavily(raw)
        search_results.extend(normalized)  # extend not append

    return {
        "queries": selected_queries,
        "searched_queries": selected_queries,
        "search_results": search_results,
    }
