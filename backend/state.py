
from typing import Optional, Annotated, List, Sequence
from backend.research.schemas import ResearchNote
from backend.tools.normalizers import SearchResult
from backend.writer.schemas import (
    CitationValidation,
    EvidenceCuration,
    InvestmentReport,
)

# This is the inbuilt message state which store all the message running in graph during persistent memory like current memory
from langgraph.graph import MessagesState


MAX_ACCUMULATED_RESEARCH_NOTES = 40


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def add_unique_strings(left: list[str] | None, right: list[str] | None) -> list[str]:
    merged = []
    seen = set()

    for value in (left or []) + (right or []):
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        merged.append(value)

    return merged


def add_unique_research_notes(
    left: list[ResearchNote] | None,
    right: list[ResearchNote] | None,
) -> list[ResearchNote]:
    # Keep the graph-level state bounded too. Node-level limits are not enough
    # because LangGraph reducers merge outputs across research rounds.
    merged = []
    seen = set()

    for note in (left or []) + (right or []):
        note_key = (
            _normalize_text(note.content),
            _normalize_text(note.source_url),
            _normalize_text(note.query),
        )
        if note_key in seen:
            continue

        seen.add(note_key)
        merged.append(note)

        if len(merged) >= MAX_ACCUMULATED_RESEARCH_NOTES:
            break

    return merged


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
    searched_queries: Annotated[list[str], add_unique_strings]
    
    # This is how web scarapping data will be come for now it is travily we will do normalize it later
    # Information retrival node
    # Normalized search results from the retriever (currently Tavily)
    search_results: list[SearchResult] = []

    
    # Notes extracted from search results and used by the writer
    # research_notes: list[str] = []
    # research_notes: Annotated[list[str], operator.add]
    research_notes: Annotated[list[ResearchNote], add_unique_research_notes]
    
    # Number of research loops performed
    research_iterations: int = 0
    
    # Coverage Checker Output

    is_sufficient: bool | None = None

    missing_information: list[str] = []

    coverage_assessment: str | None = None

    evidence_curation: EvidenceCuration | None = None

    investment_report: InvestmentReport | None = None

    citation_validation: CitationValidation | None = None

    # One bounded writer retry is allowed after citation validation fails.
    report_revision_count: int = 0

    pdf_path: str | None = None
    pdf_error: str | None = None
