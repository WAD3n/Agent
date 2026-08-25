import argparse
import sys

from openai import RateLimitError

from agent.graph import AVAILABLE_MODELS, DEFAULT_MODEL, build_graph
from agent.trace import stream_steps

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


def run_with_trace(app, question: str, model: str) -> None:
    step_number = 0
    for node_name, new_messages, _ in stream_steps(app, question, model):
        for message in new_messages:
            step_number += 1
            print_step(node_name, message, step_number)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent CLI")
    parser.add_argument(
        "--model",
        choices=AVAILABLE_MODELS,
        default=DEFAULT_MODEL,
        help=f"Groq model to use (default: {DEFAULT_MODEL})",
    )
    return parser.parse_args()


def main() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")

    args = parse_args()
    app = build_graph()
    print(f"Agent CLI. Model: {args.model}. Type a question (exit / quit / ctrl+c to leave).")

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
            run_with_trace(app, question, args.model)
        except RateLimitError:
            print("Groq rate limit reached (free tier). Wait a bit and try again.")
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
