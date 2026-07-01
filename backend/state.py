
import operator
from typing import Optional, Annotated, List, Sequence


# This is the inbuilt message state which store all the message running in graph during persistent memory like current memory
from langgraph.graph import MessagesState

class InvestMindInputState(MessagesState):
    """Input state for the full agent - only contains messages from user input."""
    pass

class InvestMindState(MessagesState):
    """
    Shared state for the InvestMind LangGraph workflow.

    This state is passed between all nodes in the graph.
    Each agent reads from and writes to this object.
    """
    
    # Whether another clarification round is required
    need_clarification: bool | None = None

    # Question to ask the user if clarification is needed
    clarification_question: str | None = None

    # Final research brief produced by the planner
    research_brief: str | None = None
    

# 