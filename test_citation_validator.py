from backend.research.schemas import ResearchNote
import backend.writer.nodes.citation_validator as validator_module
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
    def __init__(self, response):
        self.response = response
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return self.response


class FakeLLM:
    def __init__(self, response):
        self.schema = None
        self.structured_llm = FakeStructuredLLM(response)

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def make_state(report):
    return {
        "required_information": ["Revenue growth"],
        "investment_report": report,
        "evidence_curation": EvidenceCuration(
            groups=[
                EvidenceGroup(
                    requirement="Revenue growth",
                    selected_note_ids=[1],
                    conflicting_note_ids=[],
                )
            ]
        ),
        "research_notes": [
            ResearchNote(
                content="Fiscal 2024 revenue was $60.9 billion.",
                source_url="https://example.com/results",
                query="fiscal 2024 revenue",
            )
        ],
    }


def make_report(analysis_content, cited_note_ids):
    return InvestmentReport(
        title="Investment Report",
        executive_summary=CitedContent(
            content="Fiscal 2024 revenue was $60.9 billion [N1].",
            cited_note_ids=[1],
        ),
        sections=[
            ReportSection(
                requirement="Revenue growth",
                heading="Revenue Growth",
                analysis=CitedContent(
                    content=analysis_content,
                    cited_note_ids=cited_note_ids,
                ),
            )
        ],
        evidence_limitations=[],
    )


def test_validate_cited_content_rejects_invalid_and_mismatched_ids():
    issues = validator_module.validate_cited_content(
        "Revenue growth",
        CitedContent(
            content="Revenue was $60.9 billion [N9].",
            cited_note_ids=[1],
        ),
        allowed_note_ids={1},
    )

    assert {issue.issue_type for issue in issues} == {
        "invalid_citation",
        "citation_mismatch",
    }


def test_citation_validator_returns_semantic_issue(monkeypatch):
    fake_llm = FakeLLM(
        CitationValidation(
            is_valid=False,
            issues=[
                CitationIssue(
                    location="Revenue growth",
                    claim="Revenue growth makes Nvidia a guaranteed winner.",
                    cited_note_ids=[1],
                    issue_type="unsupported_claim",
                    explanation="The evidence reports revenue but no guaranteed outcome.",
                )
            ],
        )
    )
    monkeypatch.setattr(validator_module, "llm", fake_llm)

    result = validator_module.citation_validator_node(
        make_state(
            make_report(
                "Revenue growth makes Nvidia a guaranteed winner [N1].",
                [1],
            )
        )
    )

    validation = result["citation_validation"]

    assert fake_llm.schema is CitationValidation
    assert validation.is_valid is False
    assert validation.issues[0].issue_type == "unsupported_claim"
    assert "Fiscal 2024 revenue was $60.9 billion" in (
        fake_llm.structured_llm.messages[1].content
    )


def test_citation_validator_accepts_supported_report(monkeypatch):
    fake_llm = FakeLLM(CitationValidation(is_valid=True, issues=[]))
    monkeypatch.setattr(validator_module, "llm", fake_llm)

    result = validator_module.citation_validator_node(
        make_state(
            make_report(
                "Fiscal 2024 revenue was $60.9 billion [N1].",
                [1],
            )
        )
    )

    validation = result["citation_validation"]

    assert validation.is_valid is True
    assert validation.issues == []


def test_citation_validator_rejects_requirement_mismatch(monkeypatch):
    fake_llm = FakeLLM(CitationValidation(is_valid=True, issues=[]))
    monkeypatch.setattr(validator_module, "llm", fake_llm)
    state = make_state(
        make_report(
            "Fiscal 2024 revenue was $60.9 billion [N1].",
            [1],
        )
    )
    state["required_information"] = ["Different requirement"]

    result = validator_module.citation_validator_node(state)
    validation = result["citation_validation"]

    assert validation.is_valid is False
    assert any(
        issue.issue_type == "requirement_mismatch"
        for issue in validation.issues
    )
