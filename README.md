# 📚 Study Buddy — Multi-Agent RAG Assistant

An AI study assistant that lets you upload class notes (PDFs) and interact with three specialized agents built on top of a Retrieval-Augmented Generation (RAG) pipeline.

- **💬 Q&A Agent** — Ask questions and get answers grounded in your notes (with source citations).
- **📝 Summarizer Agent** — Get structured, bullet-pointed summaries of any topic.
- **❓ Quiz Agent** — Generate practice quizzes with multiple-choice and short-answer questions.

100% free to run — no paid APIs, no cloud services.

## Architecture

```
                 ┌────────────────┐
   PDF upload ─► │ Chunker (word- │
                 │ level, 400/50) │
                 └───────┬────────┘
                         ▼
                 ┌────────────────────────┐
                 │ Embedder               │
                 │ (sentence-transformers │
                 │  all-MiniLM-L6-v2)     │
                 └───────┬────────────────┘
                         ▼
                 ┌────────────────┐
                 │  ChromaDB      │  (persistent, local)
                 │  vector store  │
                 └───────┬────────┘
                         │  top-k retrieval
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│  Retriever │   │ Summarizer │   │    Quiz    │
│   Agent    │   │   Agent    │   │   Agent    │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘
      └────────────────┼────────────────┘
                       ▼
              ┌────────────────┐
              │   Groq LLM     │  (openai/gpt-oss-120b, free tier)
              └────────────────┘
```

## Tech stack

| Component | Tool | Cost |
|-----------|------|------|
| UI | Streamlit | Free |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, runs on CPU) | Free (local) |
| Vector DB | ChromaDB | Free (local) |
| LLM | Groq API — `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`) | Free tier |
| PDF parsing | pypdf (+ PyMuPDF + RapidOCR fallback for scanned/image PDFs) | Free |

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/study-buddy.git
cd study-buddy

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate           # macOS/Linux
venv\Scripts\activate              # Windows

# 3. Install dependencies (~2-3 minutes, first time downloads sentence-transformers model)
pip install -r requirements.txt

# 4. Get a free Groq API key
#    Sign up at https://console.groq.com/keys and create a key.

# 5. Copy .env.example to .env and paste your key
cp .env.example .env
# then edit .env and set GROQ_API_KEY=gsk_...

# 6. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload any PDF (a textbook chapter, class notes, an old paper) and click through the tabs. Scanned/image-only PDFs are handled automatically via OCR (400 DPI rendering + RapidOCR).

## 🌍 Deploy to the web (no installs for your users)

To share the app as a public URL so clients/students just open a link in their browser — no downloads, no Python, nothing to install — follow **[DEPLOY.md](DEPLOY.md)** (Streamlit Community Cloud, free, ~10 minutes one-time setup).

## Project structure

```
study-buddy/
├── app.py                      # Streamlit UI + agent orchestration
├── config.py                   # Settings from .env (local) or st.secrets (cloud)
├── requirements.txt
├── DEPLOY.md                   # Step-by-step web deployment guide
├── .env.example
├── .streamlit/
│   └── secrets.toml.example    # Cloud secrets format reference
├── agents/
│   ├── retriever_agent.py      # RAG-based Q&A
│   ├── summarizer_agent.py     # Structured summarization
│   └── quiz_agent.py           # Quiz generation
└── rag/
    ├── chunker.py              # PDF → chunks (text layer + OCR fallback @ 400 DPI)
    ├── embedder.py             # sentence-transformers wrapper
    └── vectorstore.py          # ChromaDB persistent store
```

## What I learned
- Building a Retrieval-Augmented Generation (RAG) pipeline from scratch (chunk → embed → index → retrieve → generate)
- Designing a multi-agent system where each agent has a focused prompt and role
- Working with a local vector database (ChromaDB) and open-source embeddings
- Integrating an LLM API (Groq) and managing prompts, temperature, and token limits
- Streamlit session state for keeping expensive objects (model, DB) alive across reruns

## Roadmap
- [ ] Support multiple document formats (DOCX, TXT, web URLs)
- [ ] Add a "Study Plan" agent that produces a daily plan
- [ ] Migrate agent orchestration to LangGraph for explicit state machines
- [ ] Evaluate retrieval quality with a small labelled set (recall@k, MRR)

## License
MIT
