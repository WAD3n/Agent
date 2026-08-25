import json
import os
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph
from openai import BadRequestError

from agent.llm_client import get_groq_client
from agent.tool_registry import TOOL_FUNCTIONS, TOOL_SCHEMAS

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MODEL = DEFAULT_MODEL  # kept for backwards compatibility (e.g. eval/judge.py)

# Chat-capable models available on the free Groq tier for this account
# (see `client.models.list()`; audio/prompt-guard models are excluded).
AVAILABLE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3.6-27b",
    "groq/compound",
    "groq/compound-mini",
    "allam-2-7b",
]

MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools: web search, a calculator, "
    "and a knowledge base. Use a tool when it helps answer the question, "
    "otherwise answer directly."
)


class AgentState(TypedDict):
    messages: list[dict]
    steps: int
    prompt_tokens: int
    completion_tokens: int
    model: str
    forced_tool: str | None


def _extract_usage(response) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    try:
        return int(usage.prompt_tokens), int(usage.completion_tokens)
    except (AttributeError, TypeError):
        return 0, 0


def reason(state: AgentState) -> AgentState:
    client = get_groq_client()
    force_final_answer = state["steps"] >= MAX_STEPS - 1

    model = state.get("model") or DEFAULT_MODEL
    kwargs: dict = {"model": model, "messages": cast(Any, state["messages"])}
    if not force_final_answer:
        # Omit `tools` entirely when forcing a final answer: passing
        # tool_choice="none" alongside `tools` still lets the model attempt a
        # tool call on Groq, which the API then rejects with a 400.
        kwargs["tools"] = cast(Any, TOOL_SCHEMAS)
        forced_tool = state.get("forced_tool")
        if forced_tool and state["steps"] == 0:
            # Only force on the first step — forcing on every step would
            # make the agent call the same tool forever and never answer.
            kwargs["tool_choice"] = {"type": "function", "function": {"name": forced_tool}}
        else:
            kwargs["tool_choice"] = "auto"

    try:
        response = client.chat.completions.create(**kwargs)
    except BadRequestError:
        if kwargs.get("tool_choice") == "auto":
            raise
        # Forcing a specific tool isn't always honored by the model — Groq
        # then rejects the response with a 400 ("tool choice is required,
        # but model did not call a tool"). Retry once without forcing it.
        kwargs["tool_choice"] = "auto"
        response = client.chat.completions.create(**kwargs)

    message = response.choices[0].message
    prompt_tokens, completion_tokens = _extract_usage(response)

    assistant_message: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
            if tc.type == "function"
        ]

    return {
        "messages": state["messages"] + [assistant_message],
        "steps": state["steps"] + 1,
        "prompt_tokens": state.get("prompt_tokens", 0) + prompt_tokens,
        "completion_tokens": state.get("completion_tokens", 0) + completion_tokens,
    }


def call_tools(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    tool_results = []

    for tool_call in last_message.get("tool_calls", []):
        name = tool_call["function"]["name"]
        try:
            args = json.loads(tool_call["function"]["arguments"])
            output = TOOL_FUNCTIONS[name](**args)
        except Exception as exc:
            output = f"Error running tool '{name}': {exc}"

        tool_results.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(output),
            }
        )

    return {"messages": state["messages"] + tool_results, "steps": state["steps"]}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.get("tool_calls") and state["steps"] < MAX_STEPS:
        return "call_tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("reason", reason)
    graph.add_node("call_tools", call_tools)

    graph.set_entry_point("reason")
    graph.add_conditional_edges("reason", should_continue, {"call_tools": "call_tools", END: END})
    graph.add_edge("call_tools", "reason")

    return graph.compile()


def run_agent(question: str, model: str = DEFAULT_MODEL, forced_tool: str | None = None) -> AgentState:
    app = build_graph()
    initial_state: AgentState = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "steps": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "model": model,
        "forced_tool": forced_tool,
    }
    return cast(AgentState, app.invoke(initial_state))
