import pytest
from langchain_core.messages import HumanMessage
from backend.planner.graph import planner_graph

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

def run_planner(user_message: str) -> dict:
    """Run the planner graph with a single user message."""
    return planner_graph.invoke({
        "messages": [HumanMessage(content=user_message)]
    })

# ----------------------------------------------------------
# Clarification Node Tests
# ----------------------------------------------------------

class TestClarificationNode:

    def test_clear_investment_query_no_clarification(self):
        """Clear investment query should proceed without clarification."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert result["need_clarification"] is False

    def test_ambiguous_company_name_needs_clarification(self):
        """Ambiguous subject should trigger clarification."""
        result = run_planner("Tell me about Apple.")
        assert result["need_clarification"] is True
        assert result["clarification_question"] is not None
        assert len(result["clarification_question"]) > 0

    def test_missing_comparison_target_needs_clarification(self):
        """Missing comparison target should trigger clarification."""
        result = run_planner("Compare Tesla.")
        assert result["need_clarification"] is True
        assert result["clarification_question"] is not None

    def test_too_broad_request_needs_clarification(self):
        """Overly broad request should trigger clarification."""
        result = run_planner("Research AI.")
        assert result["need_clarification"] is True

    def test_clear_comparison_no_clarification(self):
        """Clear comparison with both targets should not need clarification."""
        result = run_planner("Compare Apple and Microsoft AI strategy.")
        assert result["need_clarification"] is False

    def test_brief_but_clear_query_no_clarification(self):
        """Brief query with clear intent should not need clarification."""
        result = run_planner("Is Tesla a good buy right now?")
        result = run_planner("TSMC manufacturing roadmap.")
        assert result["need_clarification"] is False

    # def test_reasoning_always_populated(self):
    #     """Reasoning field should always be populated."""
    #     result = run_planner("Analyze Nvidia as a long-term investment.")
    #     assert result["reasoning"] is not None
    #     assert len(result["reasoning"]) > 10

    def test_clarification_question_is_single_question(self):
        """Clarification question should be one question, not compound."""
        result = run_planner("Tell me about Apple.")
        if result["need_clarification"]:
            question = result["clarification_question"]
            # A compound question would have multiple question marks
            assert question.count("?") <= 1

# ----------------------------------------------------------
# Research Brief Node Tests
# ----------------------------------------------------------

class TestResearchBriefNode:

    def test_objective_is_one_sentence(self):
        """Objective must be a single sentence."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        objective = result["objective"]
        # One sentence means one full stop at most
        sentences = [s.strip() for s in objective.split(".") if s.strip()]
        assert len(sentences) <= 2  # some tolerance for LLM

    def test_constraints_max_five(self):
        """Constraints must not exceed 5 items."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert len(result["constraints"]) <= 5

    def test_required_information_max_eight(self):
        """Required information must not exceed 8 items."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert len(result["required_information"]) <= 8

    def test_required_information_not_empty(self):
        """Required information must have at least one item."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert len(result["required_information"]) >= 1

    def test_scope_is_populated(self):
        """Scope must be populated."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert result["scope"] is not None
        assert len(result["scope"]) > 0

    def test_comparison_appears_in_constraints(self):
        """If user requests comparison, it should appear in constraints."""
        result = run_planner("Compare Nvidia and AMD as investments.")
        constraints_text = " ".join(result["constraints"]).lower()
        assert "amd" in constraints_text or "nvidia" in constraints_text

    def test_time_period_appears_in_scope(self):
        """If user specifies time period, it should appear in scope."""
        result = run_planner("Analyze Nvidia financials for the last 5 years.")
        assert "5" in result["scope"] or "five" in result["scope"].lower()

    def test_no_research_performed(self):
        """Brief should not contain actual research data."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        objective = result["objective"].lower()
        # Objective should be a goal, not a finding
        assert "revenue was" not in objective
        assert "stock price" not in objective

# ----------------------------------------------------------
# Routing Tests
# ----------------------------------------------------------

class TestRouting:

    def test_clear_query_reaches_research_brief(self):
        """Clear query should populate research brief fields."""
        result = run_planner("Analyze Nvidia as a long-term investment.")
        assert result["need_clarification"] is False
        assert result["objective"] is not None
        assert result["required_information"] is not None

    def test_ambiguous_query_stops_at_clarification(self):
        """Ambiguous query should not populate research brief."""
        result = run_planner("Tell me about Apple.")
        if result["need_clarification"]:
            # If clarification needed, research brief should not be populated
            assert result.get("objective") is None or result.get("objective") == ""

# ----------------------------------------------------------
# Edge Case Tests
# ----------------------------------------------------------

class TestEdgeCases:

    def test_very_long_query(self):
        """Long detailed query should not exceed field limits."""
        long_query = """
        Analyze Nvidia Corporation as a long-term investment opportunity.
        Focus on their AI GPU business, CUDA ecosystem, data center growth,
        competition from AMD and Intel, valuation metrics, risks including
        export controls and supply chain, and their automotive and robotics
        pipeline. Compare with AMD and Intel. Use last 3 years of data.
        Include quantitative metrics and cite official sources.
        """
        result = run_planner(long_query)
        assert len(result["constraints"]) <= 5
        assert len(result["required_information"]) <= 8

    def test_non_financial_query(self):
        """System should handle non-financial research queries."""
        result = run_planner("Compare Rust and Go for backend development.")
        assert result["need_clarification"] is False
        assert result["objective"] is not None

    def test_empty_constraints_still_valid(self):
        """Constraints can be empty for simple queries."""
        result = run_planner("Explain quantum computing.")
        assert isinstance(result["constraints"], list)