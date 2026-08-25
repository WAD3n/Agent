from typing import Iterator

from agent.graph import DEFAULT_MODEL, SYSTEM_PROMPT, AgentState


def build_initial_state(
    question: str, model: str = DEFAULT_MODEL, forced_tool: str | None = None
) -> AgentState:
    return {
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


def stream_steps(
    app, question: str, model: str = DEFAULT_MODEL, forced_tool: str | None = None
) -> Iterator[tuple[str, list[dict], AgentState]]:
    """Run the graph, yielding (node_name, new_messages, node_state) per super-step."""
    state = build_initial_state(question, model, forced_tool)
    seen = len(state["messages"])

    for update in app.stream(state, stream_mode="updates"):
        for node_name, node_state in update.items():
            messages = node_state["messages"]
            new_messages = messages[seen:]
            seen = len(messages)
            yield node_name, new_messages, node_state
