"""Central configuration — works locally (.env) and on Streamlit Community Cloud (secrets).

Resolution order for every setting:
  1. real environment variable (local .env via python-dotenv)
  2. Streamlit secrets (st.secrets — used on Streamlit Community Cloud, set in the
     app's "Manage secrets" dashboard, shape documented in .streamlit/secrets.toml.example)
  3. built-in default
"""
import os

try:
    # Local development: pick up .env from the project root if present.
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get(name, default=None):
    """Prefer environment variables, fall back to Streamlit secrets (cloud)."""
    val = os.environ.get(name)
    if val:
        return val
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        # Not running inside Streamlit, or no secrets file — fine.
        pass
    return default


GROQ_API_KEY = _get("GROQ_API_KEY", "")
GROQ_MODEL = _get("GROQ_MODEL", "openai/gpt-oss-120b")
