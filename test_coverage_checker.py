from pydantic import ValidationError
import pytest

import backend.research.nodes.coverage_checker as coverage_module
from backend.research.schemas import (
    CoverageCheck,
    RequiredInfoCoverage,
    ResearchNote,
)


class FakeStructuredLLM:
    def __init__(self, response):
        self.messages = None
        self.response = response

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


def make_state():
    return {
        "objective": "Evaluate Nvidia as a long-term investment.",
        "scope": "Focus on fiscal 2024 and AI/data center business.",
        "constraints": ["Prioritize official sources"],
        "required_information": [
            "Nvidia fiscal 2024 revenue",
            "Nvidia fiscal 2024 data center revenue",
        ],
        "research_notes": [
            ResearchNote(
                content="For fiscal 2024, Nvidia revenue was $60.9 billion.",
                source_url="https://investor.nvidia.com/results",
                query="Nvidia fiscal 2024 revenue official",
            ),
            ResearchNote(
                content="Fiscal-year Data Center revenue was $47.5 billion.",
                source_url="https://investor.nvidia.com/results",
                query="Nvidia fiscal 2024 data center revenue",
            ),
        ],
    }


def test_coverage_schema_forbids_extra_fields():
    with pytest.raises(ValidationError):
        CoverageCheck(
            coverage=[],
            coverage_assessment="ok",
            extra_field="not allowed",
        )

    with pytest.raises(ValidationError):
        RequiredInfoCoverage(
            item="x",
            covered=True,
            extra_field="not allowed",
        )


def test_coverage_checker_marks_sufficient_when_all_items_covered(monkeypatch):
    response = CoverageCheck(
        coverage=[
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 revenue",
                covered=True,
            ),
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 data center revenue",
                covered=True,
            ),
        ],
        coverage_assessment="Both required items are covered with quantitative notes.",
    )
    fake_llm = FakeLLM(response)
    monkeypatch.setattr(coverage_module, "llm", fake_llm)

    result = coverage_module.coverage_checker_node(make_state())

    assert fake_llm.schema is CoverageCheck
    assert result["is_sufficient"] is True
    assert result["missing_information"] == []
    assert "covered" in result["coverage_assessment"]


def test_coverage_checker_returns_searchable_gaps(monkeypatch):
    response = CoverageCheck(
        coverage=[
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 revenue",
                covered=True,
            ),
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 data center revenue",
                covered=False,
                gap_note="Data center revenue is missing.",
                gap_reason="not_yet_searched",
            ),
        ],
        coverage_assessment="One item needs another search.",
    )
    monkeypatch.setattr(coverage_module, "llm", FakeLLM(response))

    result = coverage_module.coverage_checker_node(make_state())

    assert result["is_sufficient"] is True
    assert result["missing_information"] == [
        "Nvidia fiscal 2024 data center revenue"
    ]


def test_coverage_checker_ignores_likely_unavailable_for_looping(monkeypatch):
    response = CoverageCheck(
        coverage=[
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 revenue",
                covered=True,
            ),
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 data center revenue",
                covered=False,
                gap_note="Internal customer-level revenue split is unavailable.",
                gap_reason="likely_unavailable",
            ),
        ],
        coverage_assessment="Only non-public information is missing.",
    )
    monkeypatch.setattr(coverage_module, "llm", FakeLLM(response))

    result = coverage_module.coverage_checker_node(make_state())

    assert result["is_sufficient"] is True
    assert result["missing_information"] == []


def test_coverage_checker_aligns_missing_llm_items(monkeypatch):
    response = CoverageCheck(
        coverage=[
            RequiredInfoCoverage(
                item="Nvidia fiscal 2024 revenue",
                covered=True,
            ),
            RequiredInfoCoverage(
                item="Invented item",
                covered=True,
            ),
        ],
        coverage_assessment="LLM skipped one required item.",
    )
    monkeypatch.setattr(coverage_module, "llm", FakeLLM(response))

    result = coverage_module.coverage_checker_node(make_state())

    assert result["is_sufficient"] is True
    assert result["missing_information"] == [
        "Nvidia fiscal 2024 data center revenue"
    ]
