import re


# These limits keep one research run from multiplying into dozens of Tavily
# searches and one note-extraction LLM call for every returned document.
MAX_INITIAL_QUERIES = 8
MAX_FOLLOW_UP_QUERIES = 3
MAX_TOTAL_QUERIES = 10


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query).strip().casefold()


def select_unique_queries(
    queries: list[str],
    *,
    limit: int,
    excluded: list[str] | None = None,
) -> list[str]:
    if limit <= 0:
        return []

    seen = {normalize_query(query) for query in excluded or []}
    selected = []

    for query in queries:
        cleaned_query = re.sub(r"\s+", " ", query).strip()
        normalized_query = normalize_query(cleaned_query)

        if not normalized_query or normalized_query in seen:
            continue

        seen.add(normalized_query)
        selected.append(cleaned_query)

        if len(selected) >= limit:
            break

    return selected
