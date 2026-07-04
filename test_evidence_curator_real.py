import os

import pytest

from backend.research.schemas import ResearchNote
from backend.writer.nodes.evidence_curator import evidence_curator_node


@pytest.mark.skipif(
    os.getenv("RUN_REAL_LLM_TESTS") != "1",
    reason="Set RUN_REAL_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_evidence_curator_real_llm_trace():
    required_information = [
        "Rust and Go backend performance benchmarks",
        "Rust and Go concurrency models",
    ]
    research_notes = [
        ResearchNote(
            content=(
                "In the same HTTP benchmark, the Rust service processed "
                "120,000 requests per second and the Go service processed 95,000."
            ),
            source_url="https://benchmark.example.org/rust-go-http",
            query="Rust Go HTTP benchmark",
        ),
        ResearchNote(
            content=(
                "A separate report using the same HTTP benchmark configuration "
                "measured Go at 130,000 requests per second and Rust at 80,000."
            ),
            source_url="https://independent.example.com/go-rust-benchmark",
            query="Go Rust HTTP benchmark comparison",
        ),
        ResearchNote(
            content="The Rust ownership model prevents data races at compile time.",
            source_url="https://doc.rust-lang.org/book/ch16-00-concurrency.html",
            query="Rust official concurrency ownership",
        ),
        ResearchNote(
            content="Go uses goroutines and channels as core concurrency primitives.",
            source_url="https://go.dev/doc/effective_go#concurrency",
            query="Go official concurrency goroutines channels",
        ),
        ResearchNote(
            content="Goroutines are multiplexed onto multiple operating system threads.",
            source_url="https://go.dev/doc/faq#goroutines",
            query="Go goroutine runtime official",
        ),
        ResearchNote(
            content="Rust supports message passing and shared-state concurrency.",
            source_url="https://doc.rust-lang.org/book/ch16-00-concurrency.html",
            query="Rust concurrency models official",
        ),
        ResearchNote(
            content="Go was introduced publicly in 2009.",
            source_url="https://go.dev/doc/faq#history",
            query="Go history",
        ),
        ResearchNote(
            content="The Rust ownership model prevents data races at compile time.",
            source_url="https://example.com/repeated-rust-note",
            query="Rust concurrency model",
        ),
    ]

    result = evidence_curator_node(
        {
            "required_information": required_information,
            "research_notes": research_notes,
        }
    )
    curation = result["evidence_curation"]

    print("\nEvidence curation:")
    for group in curation.groups:
        print(f"requirement={group.requirement}")
        print(f"selected_note_ids={group.selected_note_ids}")
        print(f"conflicting_note_ids={group.conflicting_note_ids}")

    assert [group.requirement for group in curation.groups] == required_information

    valid_ids = set(range(1, len(research_notes) + 1))
    for group in curation.groups:
        assert len(group.selected_note_ids) <= 5
        assert set(group.selected_note_ids) <= valid_ids
        assert set(group.conflicting_note_ids) <= valid_ids
        assert not (
            set(group.selected_note_ids) & set(group.conflicting_note_ids)
        )

    assert any(group.selected_note_ids for group in curation.groups)

    performance_group = curation.groups[0]
    performance_ids = set(performance_group.selected_note_ids)
    conflict_ids = set(performance_group.conflicting_note_ids)

    assert conflict_ids
    assert {1, 2} <= performance_ids | conflict_ids
    assert not {1, 2} <= performance_ids
