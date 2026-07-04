import os

import pytest

from backend.research.schemas import ResearchNote
from backend.writer.nodes.report_writer import report_writer_node
from backend.writer.schemas import EvidenceCuration, EvidenceGroup


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_report_writer_real_llm_trace():
    required_information = [
        "Nvidia fiscal 2024 total revenue growth",
        "Nvidia fiscal 2024 data center performance",
        "Material risks affecting Nvidia's investment outlook",
    ]
    research_notes = [
        ResearchNote(
            content=(
                "Nvidia reported fiscal 2024 revenue of $60.9 billion, "
                "up 126% from the prior year."
            ),
            source_url="https://investor.nvidia.com/results/fiscal-2024",
            query="Nvidia fiscal 2024 revenue official",
        ),
        ResearchNote(
            content=(
                "Nvidia reported fiscal 2024 Data Center revenue of "
                "$47.5 billion, up 217% from the prior year."
            ),
            source_url="https://investor.nvidia.com/results/fiscal-2024",
            query="Nvidia fiscal 2024 data center revenue official",
        ),
        ResearchNote(
            content=(
                "Nvidia's annual report states that it relies on third parties "
                "to manufacture, assemble, test, and package its products."
            ),
            source_url="https://investor.nvidia.com/financial-info/sec-filings",
            query="Nvidia annual report manufacturing risks",
        ),
        ResearchNote(
            content=(
                "Nvidia's annual report identifies competition and rapid "
                "technological change as risks to its business."
            ),
            source_url="https://investor.nvidia.com/financial-info/sec-filings",
            query="Nvidia annual report competition risks",
        ),
        ResearchNote(
            content="Nvidia was founded in 1993.",
            source_url="https://example.com/nvidia-history",
            query="Nvidia history",
        ),
    ]
    evidence_curation = EvidenceCuration(
        groups=[
            EvidenceGroup(
                requirement=required_information[0],
                selected_note_ids=[1],
                conflicting_note_ids=[],
            ),
            EvidenceGroup(
                requirement=required_information[1],
                selected_note_ids=[2],
                conflicting_note_ids=[],
            ),
            EvidenceGroup(
                requirement=required_information[2],
                selected_note_ids=[3, 4],
                conflicting_note_ids=[],
            ),
        ]
    )

    result = report_writer_node(
        {
            "objective": "Evaluate Nvidia as a long-term investment.",
            "scope": "Focus on fiscal 2024 performance and material business risks.",
            "constraints": [
                "Use only curated evidence",
                "Do not provide an unsupported buy or sell recommendation",
            ],
            "required_information": required_information,
            "research_notes": research_notes,
            "evidence_curation": evidence_curation,
        }
    )
    report = result["investment_report"]

    print("\nInvestment report:")
    print(f"title={report.title}")
    print(f"executive_summary={report.executive_summary.content}")
    print(
        "executive_summary_note_ids="
        f"{report.executive_summary.cited_note_ids}"
    )
    for section in report.sections:
        print(f"\nheading={section.heading}")
        print(f"requirement={section.requirement}")
        print(f"analysis={section.analysis.content}")
        print(f"cited_note_ids={section.analysis.cited_note_ids}")
    print(f"\nevidence_limitations={report.evidence_limitations}")

    assert [section.requirement for section in report.sections] == required_information

    allowed_note_ids = {1, 2, 3, 4}
    assert set(report.executive_summary.cited_note_ids) <= allowed_note_ids
    assert "[N" in report.executive_summary.content

    for section in report.sections:
        assert set(section.analysis.cited_note_ids) <= allowed_note_ids
        assert "[N" in section.analysis.content

    combined_report = " ".join(
        [report.executive_summary.content]
        + [section.analysis.content for section in report.sections]
    )
    assert "founded in 1993" not in combined_report.lower()
