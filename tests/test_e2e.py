import pytest

from agent.graph import run_agent

pytestmark = pytest.mark.e2e


def _final_answer(result) -> str:
    return result["messages"][-1]["content"]


def test_calculator_scenario():
    result = run_agent("What is 123 times 17? Give just the number.")
    answer = _final_answer(result)
    assert "2091" in answer


def test_search_scenario():
    result = run_agent("In which city is Anthropic headquartered? Answer in one word.")
    answer = _final_answer(result)
    assert answer.strip() != ""


def test_direct_answer_scenario_does_not_need_tools():
    result = run_agent("What is 2 + 2?")
    answer = _final_answer(result)
    assert "4" in answer


def test_agent_terminates_within_step_limit():
    result = run_agent("Calculate (3 + 4) * (5 - 2) and search who invented the calculator.")
    assert result["steps"] <= 5
    assert _final_answer(result).strip() != ""
