from backend.writer.graph import build_writer_graph


def test_writer_graph_renders_pdf_directly_after_report_writer():
    calls = {"curator": 0, "writer": 0, "pdf": 0}

    def fake_curator(_state):
        calls["curator"] += 1
        return {"evidence_curation": "curated"}

    def fake_writer(_state):
        calls["writer"] += 1
        return {"investment_report": "report"}

    def fake_pdf(state):
        calls["pdf"] += 1
        assert state["evidence_curation"] == "curated"
        assert state["investment_report"] == "report"
        return {"pdf_path": "/tmp/report.pdf", "pdf_error": None}

    graph = build_writer_graph(
        evidence_curator=fake_curator,
        report_writer=fake_writer,
        pdf_renderer=fake_pdf,
    )
    result = graph.invoke({"messages": []})

    assert calls == {"curator": 1, "writer": 1, "pdf": 1}
    assert result["pdf_path"] == "/tmp/report.pdf"
