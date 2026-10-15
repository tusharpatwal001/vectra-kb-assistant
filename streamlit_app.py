"""
Streamlit chat UI for Vectra KB Assistant.

- Reuses src.assistant.answer() as-is (no changes to src/).
- Persists chat history in the existing PostgreSQL DB via LangChain's
  PostgresChatMessageHistory (uses the same PG_DSN as ingest.py).
"""

import os
import uuid

import streamlit as st
from dotenv import load_dotenv

from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_core.messages import HumanMessage

from src.assistant import answer as kb_answer

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# ingest.py uses PG_DSN (e.g. postgresql://vectra:...@localhost:5432/vectra_kb)
PG_DSN = os.environ["PG_DSN"]
TABLE_NAME = "chat_message_history"

# LangChain's PostgresChatMessageHistory uses psycopg directly, so it accepts
# the plain "postgresql://" URL that PG_DSN already provides.
# psycopg (used by PostgresChatMessageHistory) does NOT accept the
# SQLAlchemy driver suffix "+psycopg". Strip it if present.
CHAT_DB_URL = PG_DSN.replace("postgresql+psycopg://", "postgresql://")

st.set_page_config(page_title="Vectra KB Assistant", page_icon="💬", layout="wide")


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def get_history(session_id: str) -> PostgresChatMessageHistory:
    return PostgresChatMessageHistory(
        connection_string=CHAT_DB_URL,
        session_id=session_id,
        table_name=TABLE_NAME,
    )


def ensure_session() -> str:
    """Initialize session_id + load persisted messages on first render."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        history = get_history(st.session_state.session_id)
        st.session_state.messages = [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in history.messages
        ]
    return st.session_state.session_id


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("💬 Vectra KB Assistant")
    st.caption("Grounded answers · source citations · persistent history")

    st.markdown("**Session ID**")
    st.code(ensure_session(), language=None)

    if st.button("🆕 New chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### Example questions")
    EXAMPLES = [
        "My account got locked. How long until it unlocks by itself?",
        "What VPN server address should I use when working from home?",
        "What is the resolution target for a P2 ticket?",
        "How do I get a parking pass for the Gurugram office?",
        "Why is my company email not showing up in my iPhone's built-in Mail app?",
    ]
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True, key=f"ex_{hash(ex)}"):
            st.session_state.pending_question = ex
            st.rerun()


# ---------------------------------------------------------------------------
# Main chat UI
# ---------------------------------------------------------------------------
st.title("Vectra Knowledge Base Assistant")
st.caption(
    "Ask questions grounded in the KB. Answers include citations when available."
)

# Replay existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📚 Sources"):
                for c in msg["citations"]:
                    st.markdown(f"- `{c}`")
        if msg.get("abstained"):
            st.caption("⚠️ No supporting KB article found — abstained.")

# Input (typed or from an example button)
user_input = st.chat_input("Ask a question about the knowledge base…")
if not user_input and st.session_state.get("pending_question"):
    user_input = st.session_state.pop("pending_question")

if user_input:
    # 1. Render + store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Persist user message
    history = get_history(st.session_state.session_id)
    history.add_user_message(user_input)

    # 3. Call existing assistant (unchanged src/)
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base…"):
            result = kb_answer(user_input)  # -> {"answer", "citations", "abstained"}
        st.markdown(result["answer"])
        if result.get("citations"):
            with st.expander("📚 Sources"):
                for c in result["citations"]:
                    st.markdown(f"- `{c}`")
        if result.get("abstained"):
            st.caption("⚠️ No supporting KB article found — abstained.")

    # 4. Persist assistant reply + cache in session
    history.add_ai_message(result["answer"])
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result.get("citations", []),
        "abstained": result.get("abstained", False),
    })