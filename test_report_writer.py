from backend.research.schemas import ResearchNote
import backend.writer.nodes.report_writer as writer_module
from backend.writer.schemas import (
    CitationIssue,
    CitationValidation,
    CitedContent,
    EvidenceCuration,
    EvidenceGroup,
    InvestmentReport,
    ReportSection,
)


class FakeStructuredLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return InvestmentReport(
            title="Nvidia Investment Evidence Report",
            executive_summary=CitedContent(
                content="Nvidia reported strong revenue growth [N1].",
                cited_note_ids=[1],
            ),
            sections=[
                ReportSection(
                    requirement="Nvidia fiscal 2024 revenue growth",
                    heading="Revenue Growth",
                    analysis=CitedContent(
                        content="Fiscal 2024 revenue was $60.9 billion [N1].",
                        cited_note_ids=[1],
                    ),
                )
            ],
            evidence_limitations=[],
        )


class FakeLLM:
    def __init__(self):
        self.schema = None
        self.structured_llm = FakeStructuredLLM()

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def test_report_writer_uses_only_curated_evidence(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(writer_module, "llm", fake_llm)

    result = writer_module.report_writer_node(
        {
            "objective": "Evaluate Nvidia as a long-term investment.",
            "scope": "Fiscal 2024",
            "constraints": ["Use official evidence"],
            "required_information": ["Nvidia fiscal 2024 revenue growth"],
            "research_notes": [
                ResearchNote(
                    content="Fiscal 2024 revenue was $60.9 billion.",
                    source_url="https://investor.nvidia.com/results",
                    query="Nvidia fiscal 2024 revenue",
                ),
                ResearchNote(
                    content="Nvidia was founded in 1993.",
                    source_url="https://example.com/history",
                    query="Nvidia history",
                ),
            ],
            "evidence_curation": EvidenceCuration(
                groups=[
                    EvidenceGroup(
                        requirement="Nvidia fiscal 2024 revenue growth",
                        selected_note_ids=[1],
                        conflicting_note_ids=[],
                    )
                ]
            ),
        }
    )

    human_message = fake_llm.structured_llm.messages[1].content

    assert fake_llm.schema is InvestmentReport
    assert result["investment_report"].title == "Nvidia Investment Evidence Report"
    assert "Fiscal 2024 revenue was $60.9 billion" in human_message
    assert "Nvidia was founded in 1993" not in human_message
    assert "[N1]" in human_message


def test_format_curated_evidence_includes_conflicts():
    notes = [
        ResearchNote(
            content="Revenue was $10 billion.",
            source_url="https://example.com/one",
            query="company revenue",
        ),
        ResearchNote(
            content="Revenue was $7 billion.",
            source_url="https://example.com/two",
            query="company revenue",
        ),
    ]
    curation = EvidenceCuration(
        groups=[
            EvidenceGroup(
                requirement="Company revenue",
                selected_note_ids=[1],
                conflicting_note_ids=[2],
            )
        ]
    )

    formatted = writer_module.format_curated_evidence(notes, curation)

    assert "[N1] Revenue was $10 billion" in formatted
    assert "[N2] Revenue was $7 billion" in formatted
    assert "Conflicting evidence:" in formatted


def test_report_writer_includes_validation_feedback_on_revision(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(writer_module, "llm", fake_llm)
    state = {
        "objective": "Evaluate Nvidia as an investment.",
        "scope": "Fiscal 2024",
        "constraints": [],
        "required_information": ["Nvidia fiscal 2024 revenue growth"],
        "research_notes": [
            ResearchNote(
                content="Fiscal 2024 revenue was $60.9 billion.",
                source_url="https://investor.nvidia.com/results",
                query="Nvidia fiscal 2024 revenue",
            )
        ],
        "evidence_curation": EvidenceCuration(
            groups=[
                EvidenceGroup(
                    requirement="Nvidia fiscal 2024 revenue growth",
                    selected_note_ids=[1],
                )
            ]
        ),
        "citation_validation": CitationValidation(
            is_valid=False,
            issues=[
                CitationIssue(
                    location="executive_summary",
                    claim="Nvidia is a guaranteed winner.",
                    cited_note_ids=[1],
                    issue_type="unsupported_claim",
                    explanation="The evidence does not support a guaranteed outcome.",
                )
            ],
        ),
        "report_revision_count": 0,
    }

    result = writer_module.report_writer_node(state)
    human_message = fake_llm.structured_llm.messages[1].content

    assert result["report_revision_count"] == 1
    assert "unsupported_claim" in human_message
    assert "guaranteed outcome" in human_message
