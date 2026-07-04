from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import report_writer_llm as llm
from backend.state import InvestMindState
from backend.writer.prompts.report_writer import REPORT_WRITER_PROMPT
from backend.writer.schemas import EvidenceCuration, InvestmentReport


def format_curated_evidence(
    research_notes,
    evidence_curation: EvidenceCuration,
) -> str:
    notes_by_id = {
        note_id: note
        for note_id, note in enumerate(research_notes, start=1)
    }
    formatted_groups = []

    for group in evidence_curation.groups:
        lines = [f"Requirement: {group.requirement}", "Selected evidence:"]

        for note_id in group.selected_note_ids:
            note = notes_by_id.get(note_id)
            if note is None:
                continue
            lines.append(
                f"- [N{note_id}] {note.content} "
                f"[source: {note.source_url}; query: {note.query}]"
            )

        if not group.selected_note_ids:
            lines.append("- No selected evidence")

        lines.append("Conflicting evidence:")
        conflict_found = False

        for note_id in group.conflicting_note_ids:
            note = notes_by_id.get(note_id)
            if note is None:
                continue
            conflict_found = True
            lines.append(
                f"- [N{note_id}] {note.content} "
                f"[source: {note.source_url}; query: {note.query}]"
            )

        if not conflict_found:
            lines.append("- None")

        formatted_groups.append("\n".join(lines))

    return "\n\n".join(formatted_groups)


def format_revision_feedback(citation_validation) -> str:
    if citation_validation is None or citation_validation.is_valid:
        return "No revision feedback. Write the initial report."

    return "\n".join(
        (
            f"- location={issue.location}; type={issue.issue_type}; "
            f"claim={issue.claim}; explanation={issue.explanation}"
        )
        for issue in citation_validation.issues
    ) or "The previous report failed validation. Remove unsupported content."


def report_writer_node(state: InvestMindState):
    objective = state["objective"]
    scope = state.get("scope")
    constraints = state.get("constraints", [])
    required_information = state["required_information"]
    research_notes = state["research_notes"]
    evidence_curation = state.get("evidence_curation")
    citation_validation = state.get("citation_validation")
    revision_count = state.get("report_revision_count", 0)

    if evidence_curation is None:
        evidence_curation = EvidenceCuration(groups=[])

    curated_evidence = format_curated_evidence(
        research_notes,
        evidence_curation,
    )
    structured_llm = llm.with_structured_output(InvestmentReport)

    response = structured_llm.invoke(
        [
            SystemMessage(content=REPORT_WRITER_PROMPT),
            HumanMessage(
                content=f"""
Objective:
{objective}

Scope:
{scope}

Constraints:
{constraints}

Required Information:
{required_information}

Curated Evidence:
{curated_evidence or "No curated evidence available."}

Revision Feedback:
{format_revision_feedback(citation_validation)}
"""
            ),
        ]
    )

    is_revision = citation_validation is not None and not citation_validation.is_valid

    return {
        "investment_report": response,
        "report_revision_count": revision_count + 1 if is_revision else revision_count,
    }
