from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import evidence_curator_llm as llm
from backend.state import InvestMindState
from backend.writer.prompts.evidence_curator import EVIDENCE_CURATOR_PROMPT
from backend.writer.schemas import EvidenceCuration , EvidenceGroup


MAX_SELECTED_NOTES = 5


def clean_note_ids(
    note_ids: list[int],
    note_count: int,
    *,
    excluded_ids: set[int] | None = None,
) -> list[int]:
    excluded_ids = excluded_ids or set()
    cleaned_ids = []
    seen_ids = set(excluded_ids)

    for note_id in note_ids:
        # IDs start at 1 and cannot exceed available notes.
        if note_id < 1 or note_id > note_count:
            continue

        if note_id in seen_ids:
            continue

        seen_ids.add(note_id)
        cleaned_ids.append(note_id)

        if len(cleaned_ids) >= MAX_SELECTED_NOTES:
            break

    return cleaned_ids

def sanitize_evidence_curation(
    response: EvidenceCuration,
    required_information: list[str],
    note_count: int,
) -> EvidenceCuration:
    groups_by_requirement = {
        group.requirement: group
        for group in response.groups
        if group.requirement in required_information
    }

    sanitized_groups = []

    for requirement in required_information:
        group = groups_by_requirement.get(requirement)

        if group is None:
            sanitized_groups.append(
                EvidenceGroup(
                    requirement=requirement,
                    selected_note_ids=[],
                    conflicting_note_ids=[],
                )
            )
            continue

        selected_ids = clean_note_ids(
            group.selected_note_ids,
            note_count,
        )

        conflicting_ids = clean_note_ids(
            group.conflicting_note_ids,
            note_count,
            excluded_ids=set(selected_ids),
        )

        sanitized_groups.append(
            EvidenceGroup(
                requirement=requirement,
                selected_note_ids=selected_ids,
                conflicting_note_ids=conflicting_ids,
            )
        )

    return EvidenceCuration(groups=sanitized_groups)



def evidence_curator_node(state: InvestMindState):
    research_notes = state["research_notes"]
    required_information = state["required_information"]

    if not research_notes:
        return {"evidence_curation": EvidenceCuration(groups=[])}

    notes_formatted = "\n".join(
        (
            f"[{note_id}] {note.content} "
            f"| source: {note.source_url} "
            f"| query: {note.query}"
        )
        for note_id, note in enumerate(research_notes, start=1)
    )

    structured_llm = llm.with_structured_output(EvidenceCuration)

    response = structured_llm.invoke(
        [
            SystemMessage(content=EVIDENCE_CURATOR_PROMPT),
            HumanMessage(
                content=f"""
Required Information:
{required_information}

Research Notes:
{notes_formatted}
"""
            ),
        ]
    )

    evidence_curation = sanitize_evidence_curation(
    response=response,
    required_information=required_information,
    note_count=len(research_notes),
)

    return {"evidence_curation": evidence_curation}
