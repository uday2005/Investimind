from backend.state import InvestMindState
from backend.research.nodes.information_planner import information_planner_node

state = InvestMindState(
    research_brief="""
    Research the impact of US interest rates on the banking sector.
"""
)

response = information_planner_node(state)

print("===== Information Planner Output =====")
print(response)

print("\n===== Required Information =====")
for i, item in enumerate(response["required_information"], start=1):
    print(f"{i}. {item}")