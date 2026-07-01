from langchain_core.messages import HumanMessage

from backend.state import InvestMindState
from backend.planner.nodes.clarification import clarification_node

state = InvestMindState(
    messages=[
        HumanMessage(
            content="Research Apple abour its earning in 2025 year"
        )
    ]
)

response = clarification_node(state)

print(response)