import json
import os
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph

from agent.llm_client import get_groq_client
from agent.tool_registry import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools: web search, a calculator, "
    "and a knowledge base. Use a tool when it helps answer the question, "
    "otherwise answer directly."
)


class AgentState(TypedDict):
    messages: list[dict]
    steps: int


def reason(state: AgentState) -> AgentState:
    client = get_groq_client()
    force_final_answer = state["steps"] >= MAX_STEPS - 1
    response = client.chat.completions.create(
        model=MODEL,
        messages=cast(Any, state["messages"]),
        tools=cast(Any, TOOL_SCHEMAS),
        tool_choice="none" if force_final_answer else "auto",
    )
    message = response.choices[0].message

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


def run_agent(question: str) -> AgentState:
    app = build_graph()
    initial_state: AgentState = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "steps": 0,
    }
    return cast(AgentState, app.invoke(initial_state))
