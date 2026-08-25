import pytest

from agent.graph import run_agent

pytestmark = pytest.mark.e2e


def _final_answer(result) -> str:
    return result["messages"][-1]["content"]


def test_calculator_scenario():
    result = run_agent("Ile to jest 123 razy 17? Podaj samą liczbę.")
    answer = _final_answer(result)
    assert "2091" in answer


def test_search_scenario():
    result = run_agent("W jakim mieście siedzibę ma Anthropic? Odpowiedz jednym słowem.")
    answer = _final_answer(result)
    assert answer.strip() != ""


def test_direct_answer_scenario_does_not_need_tools():
    result = run_agent("Ile to jest 2 + 2?")
    answer = _final_answer(result)
    assert "4" in answer


def test_agent_terminates_within_step_limit():
    result = run_agent("Oblicz (3 + 4) * (5 - 2) i wyszukaj kto wynalazł kalkulator.")
    assert result["steps"] <= 5
    assert _final_answer(result).strip() != ""
