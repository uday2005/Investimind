
import operator
from typing import Optional, Annotated, List, Sequence
from backend.research.schemas import ResearchNote
from backend.tools.normalizers import SearchResult


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

    # # Final research brief produced by the planner
    # research_brief: str | None = None
    objective: str        # objective
    scope: str
    constraints: list[str]
    
    # Information on what to reseach on which is extarcted from reseach brief so we have to make queries form these information
    required_information : list[str] = []

    # Queries which will be searched on web
    queries: list[str] = []

    # Accumulated separately so follow-up rounds cannot repeat paid searches.
    searched_queries: Annotated[list[str], operator.add]
    
    # This is how web scarapping data will be come for now it is travily we will do normalize it later
    # Information retrival node
    # Normalized search results from the retriever (currently Tavily)
    search_results: list[SearchResult] = []

    
    # Notes extracted from search results and used by the writer
    # research_notes: list[str] = []
    # research_notes: Annotated[list[str], operator.add]
    research_notes: Annotated[list[ResearchNote], operator.add]
    
    # Number of research loops performed
    research_iterations: int = 0
    
    # Coverage Checker Output

    is_sufficient: bool | None = None

    missing_information: list[str] = []

    coverage_assessment: str | None = None

    confidence: float | None = None

    
