import pytest
from pydantic import ValidationError

import backend.research.nodes.note_extractor as note_module
from backend.research.schemas import NoteExtractor, ResearchNote
from backend.tools.normalizers import SearchResult


class FakeStructuredLLM:
    def __init__(self, response=None):
        self.messages = []
        self.response = response or NoteExtractor(
            research_notes=[
                "Nvidia reported fiscal 2024 data center revenue of $47.5 billion.",
                "Nvidia data center revenue grew 217% in fiscal 2024.",
            ]
        )

    def invoke(self, messages):
        self.messages.append(messages)
        return self.response


class FailingThenPassingStructuredLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            raise Exception("429 rate limit")
        return NoteExtractor(research_notes=["Recovered note."])


class FakeLLM:
    def __init__(self, structured_llm=None):
        self.schema = None
        self.structured_llm = structured_llm or FakeStructuredLLM()

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def test_note_extractor_schema_accepts_extra_notes_for_node_trimming():
    NoteExtractor(research_notes=[])
    NoteExtractor(research_notes=["note"] * 5)
    NoteExtractor(research_notes=["note"] * 6)

    with pytest.raises(ValidationError):
        NoteExtractor(research_notes=[], extra_field="not allowed")


def test_note_extractor_trims_model_output_to_five_notes(monkeypatch):
    fake_llm = FakeLLM(
        structured_llm=FakeStructuredLLM(
            response=NoteExtractor(
                research_notes=[f"Relevant fact {index}." for index in range(7)]
            )
        )
    )
    monkeypatch.setattr(note_module, "llm", fake_llm)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Relevant facts"],
            "search_results": [
                SearchResult(
                    query="relevant facts",
                    title="Evidence",
                    url="https://example.com/evidence",
                    content="Seven relevant facts.",
                )
            ],
        }
    )

    assert len(result["research_notes"]) == 5


def test_note_extractor_respects_global_note_budget(monkeypatch):
    fake_llm = FakeLLM(
        structured_llm=FakeStructuredLLM(
            response=NoteExtractor(
                research_notes=["New fact one.", "New fact two."]
            )
        )
    )
    monkeypatch.setattr(note_module, "llm", fake_llm)

    existing_notes = [
        ResearchNote(
            content=f"Existing fact {index}.",
            query="past query",
            source_url="https://example.com/past",
        )
        for index in range(39)
    ]
    result = note_module.note_extractor_node(
        {
            "required_information": ["Relevant facts"],
            "research_notes": existing_notes,
            "search_results": [
                SearchResult(
                    query="new facts",
                    title="New evidence",
                    url="https://example.com/new",
                    content="Two new facts.",
                )
            ],
        }
    )

    assert [note.content for note in result["research_notes"]] == ["New fact one."]


def test_note_extractor_empty_search_results_returns_no_notes(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(note_module, "llm", fake_llm)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Nvidia data center revenue"],
            "search_results": [],
        }
    )

    assert result == {"research_notes": []}
    assert fake_llm.schema is None


def test_note_extractor_attaches_source_metadata(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(note_module, "llm", fake_llm)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Nvidia data center revenue"],
            "search_results": [
                SearchResult(
                    query="Nvidia data center revenue 2024",
                    title="NVIDIA FY2024 results",
                    url="https://investor.nvidia.com/results",
                    content="Nvidia reported fiscal 2024 data center revenue of $47.5 billion.",
                )
            ],
        }
    )

    assert fake_llm.schema is NoteExtractor
    assert len(result["research_notes"]) == 2
    assert result["research_notes"][0].source_url == "https://investor.nvidia.com/results"
    assert result["research_notes"][0].query == "Nvidia data center revenue 2024"
    assert result["research_notes"][0].content.startswith("Nvidia reported")


def test_note_extractor_prompt_message_includes_required_context(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(note_module, "llm", fake_llm)

    note_module.note_extractor_node(
        {
            "required_information": ["Nvidia data center revenue"],
            "search_results": [
                SearchResult(
                    query="Nvidia data center revenue 2024",
                    title="NVIDIA FY2024 results",
                    url="https://investor.nvidia.com/results",
                    content="Nvidia reported fiscal 2024 data center revenue of $47.5 billion.",
                )
            ],
        }
    )

    human_message = fake_llm.structured_llm.messages[0][1].content

    assert "Nvidia data center revenue" in human_message
    assert "NVIDIA FY2024 results" in human_message
    assert "https://investor.nvidia.com/results" in human_message
    assert "Nvidia reported fiscal 2024 data center revenue" in human_message


def test_note_extractor_retries_rate_limits(monkeypatch):
    structured_llm = FailingThenPassingStructuredLLM()
    fake_llm = FakeLLM(structured_llm=structured_llm)
    monkeypatch.setattr(note_module, "llm", fake_llm)
    monkeypatch.setattr(note_module.time, "sleep", lambda _: None)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Nvidia data center revenue"],
            "search_results": [
                SearchResult(
                    query="Nvidia data center revenue 2024",
                    title="NVIDIA FY2024 results",
                    url="https://investor.nvidia.com/results",
                    content="Nvidia reported fiscal 2024 data center revenue of $47.5 billion.",
                )
            ],
        }
    )

    assert structured_llm.calls == 2
    assert result["research_notes"][0].content == "Recovered note."


def test_note_extractor_dedupes_repeated_notes(monkeypatch):
    fake_llm = FakeLLM(
        structured_llm=FakeStructuredLLM(
            response=NoteExtractor(
                research_notes=[
                    "Nvidia fiscal 2024 revenue was $60.9 billion.",
                    "Nvidia fiscal 2024 revenue was $60.9 billion.",
                    "Nvidia fiscal 2024 revenue was $60.9 billion, up 126%.",
                ]
            )
        )
    )
    monkeypatch.setattr(note_module, "llm", fake_llm)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Nvidia fiscal 2024 revenue"],
            "search_results": [
                SearchResult(
                    query="Nvidia fiscal 2024 revenue official earnings",
                    title="NVIDIA FY2024 results",
                    url="https://investor.nvidia.com/results",
                    content="For fiscal 2024, revenue was $60.9 billion, up 126%.",
                )
            ],
        }
    )

    assert [note.content for note in result["research_notes"]] == [
        "Nvidia fiscal 2024 revenue was $60.9 billion.",
        "Nvidia fiscal 2024 revenue was $60.9 billion, up 126%.",
    ]


def test_note_extractor_discards_non_evidence_notes(monkeypatch):
    fake_llm = FakeLLM(
        structured_llm=FakeStructuredLLM(
            response=NoteExtractor(
                research_notes=[
                    "Performance data was not mentioned in the document.",
                    "Go uses goroutines for concurrent work.",
                ]
            )
        )
    )
    monkeypatch.setattr(note_module, "llm", fake_llm)

    result = note_module.note_extractor_node(
        {
            "required_information": ["Go concurrency model"],
            "search_results": [
                SearchResult(
                    query="Go concurrency model",
                    title="Go concurrency",
                    url="https://example.com/go",
                    content="Go uses goroutines for concurrent work.",
                )
            ],
        }
    )

    assert [note.content for note in result["research_notes"]] == [
        "Go uses goroutines for concurrent work."
    ]
