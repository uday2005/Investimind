from langgraph.graph import END, START, StateGraph

from backend.state import InvestMindState
from backend.writer.nodes.evidence_curator import evidence_curator_node
from backend.writer.nodes.pdf_renderer import pdf_renderer_node
from backend.writer.nodes.report_writer import report_writer_node


def build_writer_graph(
    evidence_curator=evidence_curator_node,
    report_writer=report_writer_node,
    pdf_renderer=pdf_renderer_node,
):
    builder = StateGraph(InvestMindState)

    builder.add_node("evidence_curator", evidence_curator)
    builder.add_node("report_writer", report_writer)
    builder.add_node("pdf_renderer", pdf_renderer)

    builder.add_edge(START, "evidence_curator")
    builder.add_edge("evidence_curator", "report_writer")
    # Temporary v1 shortcut: render the PDF directly after report writing.
    # Citation validation stays implemented, but it is bypassed until we make it
    # less strict and more reliable with real research output.
    builder.add_edge("report_writer", "pdf_renderer")
    builder.add_edge("pdf_renderer", END)

    return builder.compile()


writer_graph = build_writer_graph()
