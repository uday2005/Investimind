import re

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import citation_validator_llm as llm
from backend.state import InvestMindState
from backend.writer.prompts.citation_validator import CITATION_VALIDATOR_PROMPT
from backend.writer.schemas import (
    CitationIssue,
    CitationValidation,
    CitedContent,
)


CITATION_PATTERN = re.compile(r"\[N(\d+)\]")


def get_allowed_note_ids(evidence_curation) -> set[int]:
    allowed_note_ids = set()

    for group in evidence_curation.groups:
        allowed_note_ids.update(group.selected_note_ids)
        allowed_note_ids.update(group.conflicting_note_ids)

    return allowed_note_ids


def validate_cited_content(
    location: str,
    cited_content: CitedContent,
    allowed_note_ids: set[int],
) -> list[CitationIssue]:
    inline_ids = {
        int(note_id)
        for note_id in CITATION_PATTERN.findall(cited_content.content)
    }
    declared_ids = set(cited_content.cited_note_ids)
    issues = []

    invalid_ids = sorted((inline_ids | declared_ids) - allowed_note_ids)
    if invalid_ids:
        issues.append(
            CitationIssue(
                location=location,
                claim=cited_content.content,
                cited_note_ids=invalid_ids,
                issue_type="invalid_citation",
                explanation="Citation IDs are not present in curated evidence.",
            )
        )

    if inline_ids != declared_ids:
        issues.append(
            CitationIssue(
                location=location,
                claim=cited_content.content,
                cited_note_ids=sorted(inline_ids | declared_ids),
                issue_type="citation_mismatch",
                explanation=(
                    "Inline [N#] citations do not match the cited_note_ids field."
                ),
            )
        )

    insufficient_evidence = "insufficient evidence" in cited_content.content.lower()
    if not inline_ids and not declared_ids and not insufficient_evidence:
        issues.append(
            CitationIssue(
                location=location,
                claim=cited_content.content,
                cited_note_ids=[],
                issue_type="missing_citation",
                explanation="Report content has no supporting citation.",
            )
        )

    return issues


def format_validation_evidence(research_notes, allowed_note_ids: set[int]) -> str:
    evidence_lines = []

    for note_id, note in enumerate(research_notes, start=1):
        if note_id not in allowed_note_ids:
            continue
        evidence_lines.append(
            f"[N{note_id}] {note.content} "
            f"[source: {note.source_url}; query: {note.query}]"
        )

    return "\n".join(evidence_lines)


def citation_validator_node(state: InvestMindState):
    report = state["investment_report"]
    evidence_curation = state["evidence_curation"]
    research_notes = state["research_notes"]
    required_information = state["required_information"]
    allowed_note_ids = get_allowed_note_ids(evidence_curation)

    deterministic_issues = validate_cited_content(
        "executive_summary",
        report.executive_summary,
        allowed_note_ids,
    )

    for section in report.sections:
        deterministic_issues.extend(
            validate_cited_content(
                section.requirement,
                section.analysis,
                allowed_note_ids,
            )
        )

    returned_requirements = [section.requirement for section in report.sections]
    if returned_requirements != required_information:
        deterministic_issues.append(
            CitationIssue(
                location="report_sections",
                claim=str(returned_requirements),
                cited_note_ids=[],
                issue_type="requirement_mismatch",
                explanation=(
                    "Report sections do not exactly match required_information "
                    "in content and order."
                ),
            )
        )

    structured_llm = llm.with_structured_output(CitationValidation)
    semantic_validation = structured_llm.invoke(
        [
            SystemMessage(content=CITATION_VALIDATOR_PROMPT),
            HumanMessage(
                content=f"""
Investment Report:
{report.model_dump_json(indent=2)}

Curated Evidence:
{format_validation_evidence(research_notes, allowed_note_ids)}
"""
            ),
        ]
    )

    issues = deterministic_issues + semantic_validation.issues

    return {
        "citation_validation": CitationValidation(
            is_valid=semantic_validation.is_valid and not issues,
            issues=issues,
        )
    }
