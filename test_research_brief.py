from langchain_core.messages import HumanMessage, AIMessage

from backend.state import InvestMindState
from backend.planner.nodes.research_brief import research_brief_node


state = InvestMindState(
    messages=[
        HumanMessage(
            content="Research Apple."
        ),
        AIMessage(
            content="What aspect of Apple would you like to research?"
        ),
        HumanMessage(
            content="Research its AI strategy and compare it with Microsoft's AI strategy."
        )
    ]
)

response = research_brief_node(state)

print(response)
print()
print(type(response))
print()
print(response.research_brief)