import backend.research.nodes.follow_up_query_generator as follow_up_module
from backend.research.schemas import SearchQueries


class FakeStructuredLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return SearchQueries(
            queries=[
                "Nvidia AMD AI GPU market share 2024",
                "AMD MI300X competitive benchmark Nvidia H100",
            ]
        )


class FakeLLM:
    def __init__(self):
        self.schema = None
        self.structured_llm = FakeStructuredLLM()

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def test_follow_up_query_generator_uses_search_queries_schema(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(follow_up_module, "llm", fake_llm)

    follow_up_module.follow_up_query_generator_node(
        {
            "missing_information": ["Nvidia AI GPU competition from AMD"],
            "coverage_assessment": "Competition coverage is missing.",
            "constraints": ["Prioritize official sources"],
            "research_iterations": 1,
        }
    )

    assert fake_llm.schema is SearchQueries


def test_follow_up_query_generator_includes_context_and_increments_iterations(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(follow_up_module, "llm", fake_llm)

    result = follow_up_module.follow_up_query_generator_node(
        {
            "missing_information": ["Nvidia AI GPU competition from AMD"],
            "coverage_assessment": "Competition coverage is missing.",
            "constraints": ["Prioritize official sources"],
            "research_iterations": 1,
        }
    )

    human_message = fake_llm.structured_llm.messages[1].content

    assert result == {
        "queries": [
            "Nvidia AMD AI GPU market share 2024",
            "AMD MI300X competitive benchmark Nvidia H100",
        ],
        "research_iterations": 2,
    }
    assert "Nvidia AI GPU competition from AMD" in human_message
    assert "Competition coverage is missing." in human_message
    assert "Prioritize official sources" in human_message


def test_follow_up_query_generator_defaults_iterations_to_zero(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(follow_up_module, "llm", fake_llm)

    result = follow_up_module.follow_up_query_generator_node(
        {
            "missing_information": ["Nvidia AI GPU competition from AMD"],
            "coverage_assessment": "Competition coverage is missing.",
            "constraints": [],
        }
    )

    assert result["research_iterations"] == 1


def test_follow_up_query_generator_respects_remaining_budget(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(follow_up_module, "llm", fake_llm)

    result = follow_up_module.follow_up_query_generator_node(
        {
            "missing_information": ["Nvidia AI GPU competition from AMD"],
            "coverage_assessment": "Competition coverage is missing.",
            "constraints": [],
            "searched_queries": [f"past query {index}" for index in range(9)],
        }
    )

    assert result["queries"] == ["Nvidia AMD AI GPU market share 2024"]


def test_follow_up_query_generator_skips_llm_when_budget_is_exhausted(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(follow_up_module, "llm", fake_llm)

    result = follow_up_module.follow_up_query_generator_node(
        {
            "missing_information": ["Remaining evidence"],
            "searched_queries": [f"past query {index}" for index in range(10)],
            "research_iterations": 2,
        }
    )

    assert result == {"queries": [], "research_iterations": 3}
    assert fake_llm.schema is None
