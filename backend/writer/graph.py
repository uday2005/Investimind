from langgraph.graph import END, START, StateGraph

from backend.state import InvestMindState
from backend.writer.nodes.evidence_curator import evidence_curator_node
from backend.writer.nodes.citation_validator import citation_validator_node
from backend.writer.nodes.pdf_renderer import pdf_renderer_node
from backend.writer.nodes.report_writer import report_writer_node


def build_writer_graph(
    evidence_curator=evidence_curator_node,
    report_writer=report_writer_node,
    citation_validator=citation_validator_node,
    pdf_renderer=pdf_renderer_node,
):
    builder = StateGraph(InvestMindState)

    builder.add_node("evidence_curator", evidence_curator)
    builder.add_node("report_writer", report_writer)
    builder.add_node("citation_validator", citation_validator)
    builder.add_node("pdf_renderer", pdf_renderer)

    builder.add_edge(START, "evidence_curator")
    builder.add_edge("evidence_curator", "report_writer")
    # Deterministic, flag-only citation validation runs between the writer and
    # the PDF: it checks every [N#] resolves to a real note, records findings,
    # and never blocks the render.
    builder.add_edge("report_writer", "citation_validator")
    builder.add_edge("citation_validator", "pdf_renderer")
    builder.add_edge("pdf_renderer", END)

    return builder.compile()


writer_graph = build_writer_graph()