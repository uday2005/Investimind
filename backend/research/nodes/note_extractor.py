import logging
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import note_extractor_llm as llm
from backend.research.prompts.note_extractor import NOTE_EXTRACTOR_PROMPT
from backend.research.schemas import NoteExtractor, ResearchNote
from backend.state import InvestMindState

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 2
MAX_NOTES_PER_SOURCE = 5
MAX_TOTAL_RESEARCH_NOTES = 40
NON_EVIDENCE_PHRASES = (
    "not mentioned",
    "not provided",
    "no information",
    "not found",
    "unavailable in the document",
)


def normalize_note_for_dedupe(note: str) -> str:
    normalized = note.lower()
    normalized = re.sub(r"[^a-z0-9$%.]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def is_duplicate_note(note: str, seen_notes: set[str]) -> bool:
    normalized = normalize_note_for_dedupe(note)

    if normalized in seen_notes:
        return True

    seen_notes.add(normalized)
    return False


def is_non_evidence_note(note: str) -> bool:
    normalized = note.casefold()
    return any(phrase in normalized for phrase in NON_EVIDENCE_PHRASES)


def invoke_with_retry(structured_llm, messages):
    """Invoke an LLM call with exponential backoff on rate limits."""
    for attempt in range(MAX_RETRIES):
        try:
            return structured_llm.invoke(messages)
        except Exception as exc:
            if "429" not in str(exc):
                raise

            if attempt == MAX_RETRIES - 1:
                raise

            wait_time = INITIAL_BACKOFF ** attempt
            logger.warning(
                "Rate limit encountered. Retrying in %.1f seconds (attempt %d/%d)",
                wait_time,
                attempt + 1,
                MAX_RETRIES,
            )
            time.sleep(wait_time)


def note_extractor_node(state: InvestMindState):
    search_results = state["search_results"]
    required_information = state["required_information"]
    existing_notes = state.get("research_notes", [])
    remaining_note_budget = max(
        0,
        MAX_TOTAL_RESEARCH_NOTES - len(existing_notes),
    )

    if not search_results or remaining_note_budget == 0:
        return {"research_notes": []}

    structured_llm = llm.with_structured_output(NoteExtractor)
    required_info = "\n".join(f"- {item}" for item in required_information)

    research_notes = []
    # Include earlier rounds so repeated search results do not inflate the
    # accumulated state or the later coverage and report-writer prompts.
    seen_notes = {
        normalize_note_for_dedupe(note.content)
        for note in existing_notes
    }

    for result in search_results:
        if len(research_notes) >= remaining_note_budget:
            break

        try:
            response = invoke_with_retry(
                structured_llm,
                [
                    SystemMessage(content=NOTE_EXTRACTOR_PROMPT),
                    HumanMessage(
                        content=f"""
Required Information:
{required_info}

Title:
{result.title}

URL:
{result.url}

Query:
{result.query}

Content:
{result.content}
"""
                    ),
                ],
            )

            # The schema intentionally has no hard list limit because Groq can
            # return 6+ items and reject the whole tool call before Python sees
            # it. Accept the response, then enforce our five-note cost budget.
            for note in response.research_notes[:MAX_NOTES_PER_SOURCE]:
                if len(research_notes) >= remaining_note_budget:
                    break

                cleaned_note = note.strip()
                if (
                    not cleaned_note
                    or is_non_evidence_note(cleaned_note)
                    or is_duplicate_note(cleaned_note, seen_notes)
                ):
                    continue

                research_notes.append(
                    ResearchNote(
                        content=cleaned_note,
                        query=result.query,
                        source_url=result.url,
                    )
                )
        except Exception:
            logger.exception("Failed extracting notes from %s", result.url)

    return {"research_notes": research_notes}
