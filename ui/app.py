import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="LangChain Agent",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 LangChain Agent")
st.caption("Powered by AWS Bedrock (Claude Haiku) · Tools: Wikipedia · S3 · Python REPL")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Session")
    st.code(st.session_state.session_id, language=None)

    if st.button("🗑️ Clear history", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/history/{st.session_state.session_id}", timeout=5)
        except Exception:
            pass
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 New session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**Available tools**")
    st.markdown("🔍 `wikipedia_search` — factual lookups")
    st.markdown("📂 `s3_file_reader` — read files from S3")
    st.markdown("🐍 `python_repl` — run Python code")

    st.divider()
    st.markdown("**Demo queries**")
    demo_queries = [
        "What is the history of the Silk Road?",
        "Calculate compound interest on $10,000 at 7% for 15 years",
        "Read the file reports/summary.txt and summarize it",
        "What is quantum entanglement?",
        "What is 2 to the power of 32?",
    ]
    for q in demo_queries:
        if st.button(q, use_container_width=True, key=f"demo_{q[:20]}"):
            st.session_state._pending_message = q
            st.rerun()

# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle demo button clicks
# ---------------------------------------------------------------------------

pending = st.session_state.pop("_pending_message", None)

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

user_input = st.chat_input("Ask something...") or pending

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message": user_input,
                    },
                    timeout=60,
                )
                if resp.ok:
                    answer = resp.json()["answer"]
                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                else:
                    error_detail = resp.json().get("detail", resp.text)
                    st.error(f"Agent error: {error_detail}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to API. Make sure FastAPI is running:\n"
                    "```\nuvicorn api.main:app --reload --port 8000\n```"
                )
            except requests.exceptions.Timeout:
                st.error("Request timed out. The agent is taking too long — try a simpler query.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
