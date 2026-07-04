from backend.research.schemas import ResearchNote
import backend.writer.nodes.pdf_renderer as pdf_module
from backend.writer.schemas import (
    CitationValidation,
    CitedContent,
    InvestmentReport,
    ReportSection,
)


def make_pdf_state():
    return {
        "investment_report": InvestmentReport(
            title="Nvidia Investment Evidence Report",
            executive_summary=CitedContent(
                content="Fiscal 2024 revenue reached $60.9 billion [N1].",
                cited_note_ids=[1],
            ),
            sections=[
                ReportSection(
                    requirement="Nvidia fiscal 2024 revenue",
                    heading="Revenue Performance",
                    analysis=CitedContent(
                        content=(
                            "Fiscal 2024 revenue reached $60.9 billion, "
                            "up 126% from the prior year [N1]."
                        ),
                        cited_note_ids=[1],
                    ),
                )
            ],
            evidence_limitations=[
                "The evidence set does not include valuation multiples."
            ],
        ),
        "research_notes": [
            ResearchNote(
                content=(
                    "Nvidia reported fiscal 2024 revenue of $60.9 billion, "
                    "up 126% from the prior year."
                ),
                source_url="https://investor.nvidia.com/results",
                query="Nvidia fiscal 2024 revenue official",
            )
        ],
        "citation_validation": CitationValidation(is_valid=True, issues=[]),
    }


def test_pdf_renderer_creates_pdf_for_valid_report(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_module, "DEFAULT_PDF_OUTPUT_DIR", tmp_path)

    result = pdf_module.pdf_renderer_node(make_pdf_state())

    assert result["pdf_error"] is None
    pdf_path = tmp_path / result["pdf_path"].split("/")[-1]
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert pdf_path.stat().st_size > 1_000


def test_pdf_renderer_creates_pdf_without_citation_validation_gate(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(pdf_module, "DEFAULT_PDF_OUTPUT_DIR", tmp_path)
    state = make_pdf_state()
    state["citation_validation"] = CitationValidation(
        is_valid=False,
        issues=[],
    )

    result = pdf_module.pdf_renderer_node(state)

    assert result["pdf_error"] is None
    pdf_path = tmp_path / result["pdf_path"].split("/")[-1]
    assert pdf_path.exists()
