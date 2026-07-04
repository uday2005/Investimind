from backend.research.schemas import CoverageCheck, RequiredInfoCoverage
from backend.state import InvestMindState
from backend.llm import coverage_checker_llm as llm

from langchain_core.messages import SystemMessage, HumanMessage

from backend.research.prompts.coverage_checker import COVERAGE_CHECKER_PROMPT


def align_coverage_with_requirements(
    response: CoverageCheck,
    required_information: list[str],
) -> list[RequiredInfoCoverage]:
    coverage_by_item = {
        coverage.item: coverage
        for coverage in response.coverage
        if coverage.item in required_information
    }

    aligned_coverage = []

    for item in required_information:
        aligned_coverage.append(
            coverage_by_item.get(
                item,
                RequiredInfoCoverage(
                    item=item,
                    covered=False,
                    gap_note="Coverage checker did not return an assessment for this required item.",
                    gap_reason="not_yet_searched",
                ),
            )
        )

    return aligned_coverage


def coverage_checker_node(state: InvestMindState):

    objective = state["objective"]
    scope = state["scope"]
    constraints = state["constraints"]
    required_information = state["required_information"]
    research_notes = state["research_notes"]

    notes_formatted = "\n".join(
        f"- {n.content} [source: {n.source_url}, query: {n.query}]"
        for n in research_notes
    ) or "No research notes collected yet."

    structured_llm = llm.with_structured_output(CoverageCheck)

    response = structured_llm.invoke(
        [
            SystemMessage(content=COVERAGE_CHECKER_PROMPT),
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

Research Notes:
{notes_formatted}
"""
            ),
        ]
    )

    coverage = align_coverage_with_requirements(response, required_information)

    # Only gaps worth re-searching count toward the threshold
    searchable_gaps = [
        c.item for c in coverage
        if not c.covered and c.gap_reason != "likely_unavailable"
    ]

    # All gaps (searchable or not) still reported for visibility/logging
    missing_information = [
        c.item for c in coverage if not c.covered
    ]

    total_items = len(required_information)
    max_allowed_gaps = max(1, round(total_items * 0.2))
    is_sufficient = len(searchable_gaps) <= max_allowed_gaps

    return {
        "is_sufficient": is_sufficient,
        "missing_information": searchable_gaps,
        "coverage_assessment": response.coverage_assessment,
}
    
