import sys

from agent.graph import SYSTEM_PROMPT, build_graph

STEP_LABELS = {
    "reason": "REASON",
    "call_tools": "TOOL",
}


def print_step(node_name: str, message: dict, step_number: int) -> None:
    label = STEP_LABELS.get(node_name, node_name.upper())

    if message["role"] == "tool":
        content = message["content"]
        preview = content if len(content) <= 300 else content[:300] + " [...]"
        print(f"[{step_number}] {label} result ({message['tool_call_id']}): {preview}")
        return

    tool_calls = message.get("tool_calls")
    if tool_calls:
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]
            print(f"[{step_number}] {label} call: {name}({args})")
        return

    if message["content"]:
        print(f"[{step_number}] {label} answer: {message['content']}")


def run_with_trace(app, question: str) -> None:
    state = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "steps": 0,
    }

    seen = len(state["messages"])
    step_number = 0

    for update in app.stream(state, stream_mode="updates"):
        for node_name, node_state in update.items():
            messages = node_state["messages"]
            for message in messages[seen:]:
                step_number += 1
                print_step(node_name, message, step_number)
            seen = len(messages)


def main() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")

    app = build_graph()
    print("Agent CLI. Type a question (exit / quit / ctrl+c to leave).")

    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        try:
            run_with_trace(app, question)
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
