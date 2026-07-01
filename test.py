from pprint import pprint

from backend.state import InvestMindState

from backend.research.nodes.information_planner import (
    information_planner_node,
)

from backend.research.nodes.query_generator import (
    query_generator_node,
)

from backend.research.nodes.information_retrieval import (
    information_retrieval_node,
)

from backend.research.nodes.note_extractor import (
    note_extractor_node,
)


# ==========================================================
# Initial State
# ==========================================================

state = InvestMindState(
    research_brief="""
Compare Apple's AI strategy with Microsoft's AI strategy.

Focus on:
- AI products
- Investments
- Partnerships
- Future roadmap
"""
)

print("=" * 70)
print("INITIAL STATE")
print("=" * 70)
pprint(state)


# ==========================================================
# Information Planner
# ==========================================================

planner_output = information_planner_node(state)
state.update(planner_output)

print("\n")
print("=" * 70)
print("INFORMATION PLANNER OUTPUT")
print("=" * 70)
pprint(planner_output)

print("\n")
print("=" * 70)
print("STATE AFTER INFORMATION PLANNER")
print("=" * 70)
pprint(state)


# ==========================================================
# Query Generator
# ==========================================================

query_output = query_generator_node(state)
state.update(query_output)

print("\n")
print("=" * 70)
print("QUERY GENERATOR OUTPUT")
print("=" * 70)
pprint(query_output)

print("\n")
print("=" * 70)
print("STATE AFTER QUERY GENERATOR")
print("=" * 70)
pprint(state)


# ==========================================================
# Information Retrieval
# ==========================================================

retrieval_output = information_retrieval_node(state)
state.update(retrieval_output)

print("\n")
print("=" * 70)
print("INFORMATION RETRIEVAL OUTPUT")
print("=" * 70)

print(f"Queries Executed : {len(state['queries'])}")
print(f"Search Responses : {len(state['search_results'])}")

print("\nFirst Search Result Structure:")
print("-" * 70)

if state["search_results"]:
    pprint(state["search_results"][0])
else:
    print("No search results returned.")


# ==========================================================
# Note Extractor
# ==========================================================

notes_output = note_extractor_node(state)
state.update(notes_output)

print("\n")
print("=" * 70)
print("NOTE EXTRACTOR OUTPUT")
print("=" * 70)
pprint(notes_output)

print("\n")
print("=" * 70)
print("RESEARCH NOTES")
print("=" * 70)

for i, note in enumerate(state["research_notes"], start=1):
    print(f"{i}. {note}")


# ==========================================================
# Final State
# ==========================================================

print("\n")
print("=" * 70)
print("FINAL STATE")
print("=" * 70)
pprint(state)