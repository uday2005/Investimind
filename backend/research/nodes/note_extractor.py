from backend.research.schemas import NoteExtractor
from backend.state import InvestMindState
from backend.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage
from backend.research.prompts.note_extractor import NOTE_EXTRACTOR_PROMPT


def note_extractor_node(state: InvestMindState):

    search_results = state["search_results"]
    required_information = state["required_information"]
    structured_llm = llm.with_structured_output(
        NoteExtractor
    )

    response = structured_llm.invoke(
        [
            SystemMessage(content=NOTE_EXTRACTOR_PROMPT),
            HumanMessage(
                content=f"""
            Required Information:
            {required_information}

            Search Results:
            {search_results}
            """
            )
        ]
    )

    return {
        "research_notes": response.research_notes
    }