import streamlit as st

from agent.graph import build_graph
from agent.trace import stream_steps

MAX_REQUESTS_PER_SESSION = 15

st.set_page_config(page_title="AI Agent with Evaluation", page_icon="🤖")
st.title("AI Agent with Evaluation")
st.caption("Ask a question. The agent decides on its own whether to search the web, use a calculator, or answer directly.")


@st.cache_resource
def get_app():
    return build_graph()


if "request_count" not in st.session_state:
    st.session_state.request_count = 0


def render_trace_step(node_name: str, message: dict) -> None:
    if message["role"] == "tool":
        content = message["content"]
        preview = content if len(content) <= 300 else content[:300] + " [...]"
        st.markdown(f"↳ **tool result**: {preview}")
        return

    tool_calls = message.get("tool_calls")
    if tool_calls:
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]
            st.markdown(f"🔧 **called `{name}`** with `{args}`")
        return

    if message["content"]:
        st.markdown(f"💬 **final answer drafted**")


question = st.text_input("Your question", placeholder="e.g. What is 47 * 12?")
ask_clicked = st.button("Ask", type="primary")

if ask_clicked:
    if not question.strip():
        st.warning("Type a question first.")
    elif st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
        st.error(f"Session limit reached ({MAX_REQUESTS_PER_SESSION} questions). Refresh the page to reset.")
    else:
        st.session_state.request_count += 1
        graph_app = get_app()

        trace: list[tuple[str, dict]] = []
        final_state = None

        with st.spinner("Thinking..."):
            try:
                for node_name, new_messages, node_state in stream_steps(graph_app, question):
                    final_state = node_state
                    for message in new_messages:
                        trace.append((node_name, message))
            except Exception as exc:
                st.error(f"Error: {exc}")
                final_state = None

        if final_state is not None:
            answer = final_state["messages"][-1]["content"]
            st.markdown("### Answer")
            st.markdown(answer)

            with st.expander("What the agent did"):
                for node_name, message in trace:
                    render_trace_step(node_name, message)

            total_tokens = final_state["prompt_tokens"] + final_state["completion_tokens"]
            st.caption(f"{final_state['steps']} reasoning step(s) · {total_tokens} tokens")

st.caption(f"Questions asked this session: {st.session_state.request_count}/{MAX_REQUESTS_PER_SESSION}")
