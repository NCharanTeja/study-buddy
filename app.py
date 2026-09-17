"""Study Buddy - Multi-Agent RAG Assistant for Students.

Streamlit UI that orchestrates three agents (Retriever, Summarizer, Quiz)
over user-uploaded PDF notes using local embeddings + ChromaDB + Groq LLM.
"""
import streamlit as st
import config
from groq import Groq, AuthenticationError, RateLimitError, APIStatusError, APIConnectionError

from rag.chunker import chunk_pdf
from rag.embedder import Embedder
from rag.vectorstore import VectorStore
from agents.retriever_agent import RetrieverAgent
from agents.summarizer_agent import SummarizerAgent
from agents.quiz_agent import QuizAgent

st.set_page_config(page_title="Study Buddy", page_icon="📚", layout="wide")
st.title("📚 Study Buddy")
st.caption("Multi-agent study assistant • Upload notes → Ask, summarize, or quiz yourself")


def show_llm_error(e):
    """Display a friendly, actionable message for common Groq API failures."""
    if isinstance(e, AuthenticationError):
        st.error(
            "🔑 **Groq rejected the API key (401 Invalid API Key).**\n\n"
            "Your key in `.env` is not valid — this happens if it was copied "
            "incompletely, deleted/revoked in the Groq console, or regenerated.\n\n"
            "**Fix:** Go to https://console.groq.com/keys → create a new key → "
            "replace the whole `GROQ_API_KEY=...` line in your `.env` → restart the app "
            "(Ctrl+C, then `streamlit run app.py`)."
        )
    elif isinstance(e, RateLimitError):
        st.error(
            "⏳ **Groq rate limit reached (429).** The free tier has per-minute and "
            "per-day limits (~14,400 req/day on Llama 3.1 8B).\n\n"
            "Wait a minute and try again."
        )
    elif isinstance(e, APIConnectionError):
        st.error("🌐 **Could not reach Groq.** Check your internet connection and try again.")
    elif isinstance(e, APIStatusError) and e.status_code == 413:
        st.error("📦 **Prompt too large (413).** Try uploading a smaller PDF or fewer pages.")
    elif isinstance(e, APIStatusError):
        st.error(f"⚠️ **Groq API error (HTTP {e.status_code}).** {e}")
    else:
        st.error(f"⚠️ Unexpected error: `{e}`")


def groq_check():
    """Ping Groq with a lightweight request to validate the API key.

    Returns (True, None) if the key is accepted, else (False, exception).
    """
    try:
        client = Groq(api_key=config.GROQ_API_KEY, timeout=10)
        client.models.list()
        return True, None
    except Exception as e:
        return False, e


# Check API key (from .env locally, or Streamlit secrets on cloud)
if not config.GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not set. Copy `.env.example` to `.env` and add your free Groq key from https://console.groq.com/keys")
    st.stop()

# Initialize session state once
if "vectorstore" not in st.session_state:
    with st.spinner("Loading embedding model (first run downloads ~90MB)..."):
        st.session_state.embedder = Embedder()
        st.session_state.vectorstore = VectorStore(st.session_state.embedder)
        # ChromaDB persists on disk — recognize docs indexed in earlier sessions.
        existing = st.session_state.vectorstore.list_sources()
        st.session_state.sources = existing
        st.session_state.docs_loaded = len(existing) > 0

# Sidebar: upload
with st.sidebar:
    st.header("📄 Your material")
    uploaded = st.file_uploader("Upload a PDF (class notes, textbook chapter, etc.)", type=["pdf"])
    if uploaded and st.button("Process PDF", type="primary"):
        with st.spinner("Chunking + embedding..."):
            try:
                chunks, ocr_used = chunk_pdf(uploaded)
                if not chunks:
                    st.error(
                        "❌ **No text could be extracted from this PDF — even OCR found "
                        "nothing readable.** It may be empty, corrupted, or contain only "
                        "very low-quality images."
                    )
                else:
                    st.session_state.vectorstore.add_chunks(chunks, source=uploaded.name)
                    st.session_state.docs_loaded = True
                    if uploaded.name not in st.session_state.sources:
                        st.session_state.sources.append(uploaded.name)
                    if ocr_used:
                        st.success(
                            f"✅ Indexed {len(chunks)} chunks from {uploaded.name} "
                            "(no text layer found — used OCR 🔎)"
                        )
                    else:
                        st.success(f"✅ Indexed {len(chunks)} chunks from {uploaded.name}")
            except Exception as e:
                st.error(
                    "⚠️ **Couldn't process this PDF.** It may be corrupted, truncated, "
                    "or password-protected.\n\nDetails: `" + str(e)[:200] + "`"
                )

    if st.session_state.sources:
        st.markdown("**Loaded documents:**")
        for s in st.session_state.sources:
            st.markdown(f"- {s}")

    if st.button("🗑️ Clear all documents"):
        st.session_state.vectorstore.reset()
        st.session_state.docs_loaded = False
        st.session_state.sources = []
        st.rerun()

    st.divider()
    st.subheader("🔌 Groq connection")

    def check_groq():
        with st.spinner("Pinging Groq..."):
            ok, err = groq_check()
        st.session_state.groq_status = "ok" if ok else "fail"
        st.session_state.groq_err = err

    # One automatic check per browser session, so a bad key is caught immediately.
    if "groq_status" not in st.session_state:
        check_groq()

    if st.session_state.groq_status == "ok":
        st.success("✅ Groq key works — ask away!")
    else:
        st.warning("⚠️ Groq connection failed — asking questions will not work.")
        with st.expander("Why?"):
            show_llm_error(st.session_state.groq_err)

    if st.button("🔄 Re-test connection"):
        check_groq()
        st.rerun()

# Main: three agent tabs
tab1, tab2, tab3 = st.tabs(["💬 Ask (Q&A Agent)", "📝 Summarize Agent", "❓ Quiz Agent"])

with tab1:
    st.subheader("Ask a question about your notes")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    if st.session_state.chat and st.button("🧹 Clear chat", key="clear_chat_btn"):
        st.session_state.chat = []
        st.rerun()

    # Render past turns (newest last)
    for turn in st.session_state.chat:
        with st.chat_message("user"):
            st.write(turn["q"])
        with st.chat_message("assistant"):
            st.write(turn["a"])
            if turn.get("sources"):
                with st.expander(f"📎 Sources ({len(turn['sources'])})"):
                    for i, s in enumerate(turn["sources"], 1):
                        st.markdown(f"**Chunk {i}** — from `{s['source']}`")
                        st.text(s["text"][:400] + ("..." if len(s["text"]) > 400 else ""))

    q = st.text_input("Your question", placeholder="e.g., What is polymorphism in OOP?")
    if st.button("Ask", key="ask_btn"):
        if not st.session_state.docs_loaded:
            st.warning("Upload a PDF first (see sidebar).")
        elif not q.strip():
            st.warning("Type a question.")
        else:
            agent = RetrieverAgent(st.session_state.vectorstore)
            with st.spinner("Retrieving relevant chunks → asking the LLM..."):
                try:
                    answer, sources = agent.answer(q, history=st.session_state.chat)
                except (AuthenticationError, RateLimitError, APIStatusError, APIConnectionError) as e:
                    show_llm_error(e)
                else:
                    st.session_state.chat.append({"q": q, "a": answer, "sources": sources})
                    st.rerun()

with tab2:
    st.subheader("Get a structured summary")
    topic = st.text_input("Topic or section to summarize", placeholder="e.g., Neural networks")
    if st.button("Summarize", key="sum_btn"):
        if not st.session_state.docs_loaded:
            st.warning("Upload a PDF first.")
        elif not topic.strip():
            st.warning("Type a topic.")
        else:
            agent = SummarizerAgent(st.session_state.vectorstore)
            with st.spinner("Summarizing..."):
                try:
                    summary = agent.summarize(topic)
                except (AuthenticationError, RateLimitError, APIStatusError, APIConnectionError) as e:
                    show_llm_error(e)
                else:
                    st.markdown(summary)

with tab3:
    st.subheader("Generate a practice quiz")
    topic = st.text_input("Quiz topic", key="quiz_topic", placeholder="e.g., SQL joins")
    n = st.slider("Number of questions", 3, 10, 5)
    if st.button("Generate quiz", key="quiz_btn"):
        if not st.session_state.docs_loaded:
            st.warning("Upload a PDF first.")
        elif not topic.strip():
            st.warning("Type a topic.")
        else:
            agent = QuizAgent(st.session_state.vectorstore)
            with st.spinner("Building quiz..."):
                try:
                    quiz = agent.generate(topic, n)
                except (AuthenticationError, RateLimitError, APIStatusError, APIConnectionError) as e:
                    show_llm_error(e)
                else:
                    st.markdown(quiz)

st.markdown("---")
st.caption("Powered by sentence-transformers (local) + ChromaDB (local) + Groq (free tier). No paid APIs.")
