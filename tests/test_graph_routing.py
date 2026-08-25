from unittest.mock import MagicMock, patch

from langgraph.graph import END

from agent.graph import MAX_STEPS, call_tools, reason, should_continue


def make_llm_response(content="", tool_calls=None):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls or []
    response = MagicMock()
    response.choices = [MagicMock(message=message)]
    return response


def make_tool_call(call_id, name, arguments):
    tc = MagicMock()
    tc.id = call_id
    tc.type = "function"
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


# --- should_continue --------------------------------------------------------


def test_should_continue_routes_to_tools_when_tool_calls_present():
    state = {
        "messages": [{"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]}],
        "steps": 1,
    }
    assert should_continue(state) == "call_tools"


def test_should_continue_ends_when_no_tool_calls():
    state = {"messages": [{"role": "assistant", "content": "final answer"}], "steps": 1}
    assert should_continue(state) == END


def test_should_continue_ends_when_step_limit_reached_even_with_tool_calls():
    state = {
        "messages": [{"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]}],
        "steps": MAX_STEPS,
    }
    assert should_continue(state) == END


# --- reason ------------------------------------------------------------------


@patch("agent.graph.get_groq_client")
def test_reason_records_tool_call_from_llm(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_llm_response(
        tool_calls=[make_tool_call("call_1", "calculator", '{"expression": "2+2"}')]
    )
    mock_get_client.return_value = mock_client

    state = {"messages": [{"role": "user", "content": "ile to 2+2?"}], "steps": 0}
    result = reason(state)

    last_message = result["messages"][-1]
    assert last_message["role"] == "assistant"
    assert last_message["tool_calls"][0]["function"]["name"] == "calculator"
    assert result["steps"] == 1


@patch("agent.graph.get_groq_client")
def test_reason_records_final_answer_without_tool_call(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_llm_response(content="42")
    mock_get_client.return_value = mock_client

    state = {"messages": [{"role": "user", "content": "co to 42?"}], "steps": 0}
    result = reason(state)

    last_message = result["messages"][-1]
    assert last_message["content"] == "42"
    assert "tool_calls" not in last_message


@patch("agent.graph.get_groq_client")
def test_reason_forces_final_answer_near_step_limit(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_llm_response(content="done")
    mock_get_client.return_value = mock_client

    state = {"messages": [{"role": "user", "content": "..."}], "steps": MAX_STEPS - 1}
    reason(state)

    _, kwargs = mock_client.chat.completions.create.call_args
    assert "tools" not in kwargs
    assert "tool_choice" not in kwargs


# --- call_tools ---------------------------------------------------------------


def test_call_tools_executes_matching_tool_and_appends_result():
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "calculator", "arguments": '{"expression": "3*3"}'},
                    }
                ],
            }
        ],
        "steps": 1,
    }
    result = call_tools(state)

    tool_message = result["messages"][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_1"
    assert tool_message["content"] == "9"


def test_call_tools_reports_error_for_unknown_tool_without_raising():
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "does_not_exist", "arguments": "{}"},
                    }
                ],
            }
        ],
        "steps": 1,
    }
    result = call_tools(state)

    tool_message = result["messages"][-1]
    assert "Error" in tool_message["content"]
