"""Deterministic, flag-only citation validation.

This runs BEFORE pdf_renderer and checks that every inline [N#] citation in
the report points to a real, allowed research note. It is intentionally:

  * deterministic  -> no LLM call, so no Scout structured-output failures
  * non-blocking    -> it records findings on state and logs them, but the
                       PDF renders regardless. Nothing here can stop a report.

It answers one question per citation: "does this [N#] resolve to a curated
note?" Orphans, invalid IDs, and inline/declared mismatches get flagged.
Semantic 'does the note actually support the claim' checking is deliberately
NOT done here (that was the strict LLM layer that got the old validator
disabled). This is the safe first layer.
"""

import logging
import re

from backend.state import InvestMindState
from backend.writer.schemas import (
    CitationIssue,
    CitationValidation,
    CitedContent,
)

logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[N(\d+)\]")


def get_allowed_note_ids(evidence_curation) -> set[int]:
    """The note IDs the report is allowed to cite: everything the evidence
    curator selected or marked as conflicting."""
    allowed_note_ids: set[int] = set()
    if evidence_curation is None:
        return allowed_note_ids

    for group in evidence_curation.groups:
        allowed_note_ids.update(group.selected_note_ids)
        allowed_note_ids.update(group.conflicting_note_ids)

    return allowed_note_ids


def validate_cited_content(
    location: str,
    cited_content: CitedContent,
    allowed_note_ids: set[int],
) -> list[CitationIssue]:
    """Deterministic checks for one block of report prose."""
    inline_ids = {
        int(note_id)
        for note_id in CITATION_PATTERN.findall(cited_content.content)
    }
    declared_ids = set(cited_content.cited_note_ids)
    issues: list[CitationIssue] = []

    # 1) Any cited ID (inline or declared) that isn't an allowed note = orphan.
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

    # 2) Inline [N#] markers should match the declared cited_note_ids field.
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

    # 3) A factual block with no citation at all (unless it explicitly says
    #    the evidence was insufficient).
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


def citation_validator_node(state: InvestMindState):
    """Flag-only deterministic citation validation. Attaches findings to
    `citation_validation` and logs them; never blocks the PDF."""
    report = state.get("investment_report")
    evidence_curation = state.get("evidence_curation")
    required_information = state.get("required_information", [])

    # If there's no report somehow, record a clean/empty result and move on.
    if report is None:
        return {"citation_validation": CitationValidation(is_valid=True, issues=[])}

    allowed_note_ids = get_allowed_note_ids(evidence_curation)

    issues: list[CitationIssue] = []

    # Executive summary
    issues.extend(
        validate_cited_content(
            "executive_summary",
            report.executive_summary,
            allowed_note_ids,
        )
    )

    # Each section
    for section in report.sections:
        issues.extend(
            validate_cited_content(
                section.requirement,
                section.analysis,
                allowed_note_ids,
            )
        )

    # Sections should cover exactly the required information, in order.
    returned_requirements = [section.requirement for section in report.sections]
    if returned_requirements != required_information:
        issues.append(
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

    validation = CitationValidation(is_valid=not issues, issues=issues)

    # Flag-only: log what we found, but let the graph continue to the PDF.
    if issues:
        logger.warning(
            "Citation validation flagged %d issue(s) (report still rendered):",
            len(issues),
        )
        for issue in issues:
            logger.warning(
                "  [%s] %s | notes=%s | %s",
                issue.issue_type,
                issue.location,
                issue.cited_note_ids,
                issue.explanation,
            )
    else:
        logger.info("Citation validation passed: all citations resolve.")

    return {"citation_validation": validation}