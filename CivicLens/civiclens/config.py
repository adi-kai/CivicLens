"""API keys from .streamlit/secrets.toml. Gemini, Groq, and Tavily are optional."""
import streamlit as st

GOOGLE_KEY     = st.secrets["google"]["api_key"]
OPENSTATES_KEY = st.secrets["openstates"]["api_key"]
GROQ_KEY   = st.secrets.get("groq", {}).get("api_key", "")
TAVILY_KEY = st.secrets.get("tavily", {}).get("api_key", "")
try:
    GEMINI_KEY = st.secrets["gemini"]["api_key"]
except Exception:
    GEMINI_KEY = ""
