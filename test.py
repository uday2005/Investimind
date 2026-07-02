from pprint import pprint

from langchain_core.messages import HumanMessage

from backend.state import InvestMindState

from backend.planner.graph import planner_graph
from backend.research.graph import research_graph


state = InvestMindState(
    messages=[
        HumanMessage(
            content="""
Analyze Nvidia as a long-term investment.

Focus on:
- Business model
- Revenue
- Profitability
- AI products
- CUDA ecosystem
- Competition
- Customers
- Data center business
- Gaming business
- Automotive business
- Valuation
- Risks
- Opportunities
- Capital allocation
- Future roadmap
"""
        )
    ]
)

print("=" * 80)
print("INITIAL STATE")
print("=" * 80)

pprint(state)

# --------------------------------------------------------
# Planner
# --------------------------------------------------------

planner_output = planner_graph.invoke(state)

print("\n")
print("=" * 80)
print("PLANNER OUTPUT")
print("=" * 80)

pprint(planner_output)



# --------------------------------------------------------
# Research
# --------------------------------------------------------

research_output = research_graph.invoke(planner_output)

print("\n")
print("=" * 80)
print("RESEARCH OUTPUT")
print("=" * 80)

pprint(research_output)

print("\n")
print("=" * 80)
print("FINAL RESEARCH BRIEF")
print("=" * 80)

print(research_output["research_brief"])

print("\n")
print("=" * 80)
print("RESEARCH NOTES")
print("=" * 80)

for i, note in enumerate(research_output["research_notes"], 1):
    print(f"{i}. {note}")

print("\n")
print("=" * 80)
print("COVERAGE")
print("=" * 80)

print("Sufficient :", research_output["is_sufficient"])
print("Confidence :", research_output["confidence"])

print("\nAssessment")
print(research_output["coverage_assessment"])

print("\nMissing Information")

if research_output["missing_information"]:
    for item in research_output["missing_information"]:
        print("-", item)
else:
    print("None")

print("\n")
print("=" * 80)
print("FOLLOW-UP ITERATIONS")
print("=" * 80)

print(research_output.get("research_iterations", 0))