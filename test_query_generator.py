import pytest
from pydantic import ValidationError

import backend.research.nodes.query_generator as query_module
from backend.research.prompts.query_generator import QUERY_GENERATOR_PROMPT
from backend.research.schemas import SearchQueries


class FakeStructuredLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return SearchQueries(
            queries=[
                "Nvidia data center revenue 2022 2023 2024",
                "Nvidia data center revenue official earnings",
            ]
        )


class FakeLLM:
    def __init__(self):
        self.schema = None
        self.structured_llm = FakeStructuredLLM()

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def test_query_generator_schema_accepts_extra_queries_for_node_trimming():
    SearchQueries(queries=["Nvidia revenue 2024"])
    SearchQueries(queries=[f"query {i}" for i in range(9)])

    with pytest.raises(ValidationError):
        SearchQueries(queries=[])

    with pytest.raises(ValidationError):
        SearchQueries(queries=["Nvidia revenue 2024"], extra_field="not allowed")


def test_query_generator_node_uses_search_queries_schema(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(query_module, "llm", fake_llm)

    query_module.query_generator_node(
        {
            "required_information": ["Nvidia data center revenue by year"],
            "scope": "Last 3 years, data center segment",
            "constraints": ["Prioritize official earnings reports"],
        }
    )

    assert fake_llm.schema is SearchQueries


def test_query_generator_node_includes_required_context(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(query_module, "llm", fake_llm)

    result = query_module.query_generator_node(
        {
            "required_information": [
                "Nvidia data center revenue by year",
                "Nvidia official earnings evidence",
            ],
            "scope": "Last 3 years, data center segment",
            "constraints": ["Prioritize official earnings reports"],
        }
    )

    human_message = fake_llm.structured_llm.messages[1].content

    assert result["queries"] == [
        "Nvidia data center revenue 2022 2023 2024",
        "Nvidia data center revenue official earnings",
    ]
    assert "Nvidia data center revenue by year" in human_message
    assert "Last 3 years, data center segment" in human_message
    assert "Prioritize official earnings reports" in human_message


def test_query_generator_caps_queries_to_requirements_and_dedupes(monkeypatch):
    fake_llm = FakeLLM()
    fake_llm.structured_llm.response = None
    monkeypatch.setattr(query_module, "llm", fake_llm)

    fake_llm.structured_llm.invoke = lambda messages: SearchQueries(
        queries=[
            "Nvidia revenue 2024",
            "  Nvidia   revenue 2024  ",
            "Nvidia data center revenue 2024",
        ]
    )

    result = query_module.query_generator_node(
        {
            "required_information": ["Revenue", "Data center revenue"],
            "scope": "2024",
            "constraints": [],
        }
    )

    assert result["queries"] == [
        "Nvidia revenue 2024",
        "Nvidia data center revenue 2024",
    ]


def test_query_generator_prompt_requests_queries_not_notes():
    prompt = QUERY_GENERATOR_PROMPT.lower()

    assert "search queries" in prompt
    assert "research notes" not in prompt
