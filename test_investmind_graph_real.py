import os
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

from backend.main import investmind_graph


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_investmind_graph_real_end_to_end():
    user_request = (
        "Evaluate Microsoft as a long-term investment using fiscal 2024 "
        "evidence. Analyze total revenue and operating income growth, Azure "
        "and AI business momentum, competitive position, and material risks. "
        "Prioritize Microsoft's annual report, earnings releases, and SEC "
        "filings where available. Do not provide a buy or sell recommendation."
    )

    result = investmind_graph.invoke(
        {"messages": [HumanMessage(content=user_request)]},
        {"recursion_limit": 80},
    )

    print("\n=== FULL INVESTMIND RESULT ===")
    print(f"need_clarification={result.get('need_clarification')}")
    print(f"objective={result.get('objective')}")
    print(f"required_information={result.get('required_information')}")
    print(f"searched_queries={result.get('searched_queries')}")
    print(f"research_notes_count={len(result.get('research_notes', []))}")
    print(f"research_iterations={result.get('research_iterations')}")
    print(f"research_is_sufficient={result.get('is_sufficient')}")
    print(f"research_missing_information={result.get('missing_information')}")
    print(f"report_revision_count={result.get('report_revision_count')}")

    validation = result.get("citation_validation")
    print(f"citation_valid={validation.is_valid if validation else None}")
    if validation:
        for issue in validation.issues:
            print(
                f"citation_issue={issue.issue_type} | "
                f"{issue.location} | {issue.explanation}"
            )

    report = result.get("investment_report")
    if report:
        print(f"report_title={report.title}")
        print(f"executive_summary={report.executive_summary.content}")
        for section in report.sections:
            print(f"section={section.heading}")
            print(f"analysis={section.analysis.content}")

    print(f"pdf_path={result.get('pdf_path')}")
    print(f"pdf_error={result.get('pdf_error')}")

    assert result["need_clarification"] is False
    assert 1 <= len(result.get("searched_queries", [])) <= 10
    assert 1 <= len(result.get("research_notes", [])) <= 40
    assert report is not None
    assert result.get("pdf_error") is None
    assert result.get("pdf_path")
    assert Path(result["pdf_path"]).exists()
