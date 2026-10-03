"""Home: welcome text and section overview."""
import streamlit as st


def render():
    st.title("🗳️ CivicLens")
    st.subheader("Your complete guide to voting and civic life — in all 50 states and DC")
    st.markdown("""
    Welcome! CivicLens helps **first-time and new voters** across the United States navigate every part of the civic process.

    | Tab | What it does |
    |---|---|
    | 📍 **Polling Finder** | Locate your polling place by address — any U.S. state |
    | 📅 **Deadlines** | Election Day + your state's registration & voting resources |
    | 🏛️ **My Representatives** | Every rep who represents you — state and federal |
    | 🗺️ **Rep Map** | Interactive district map for any state, colored by party |
    | 📋 **Bill Tracker** | Browse and search active legislation in any state |
    | 🔍 **District Compare** | Compare reps for two addresses side by side — same state or different states |
    | 🗳️ **Candidates** | Live 2026 candidate research with policy positions — any state |

    **Get started →** pick any section on the left and enter your address.
    """)
    st.caption("Data: OpenStates · U.S. Census TIGERweb · Google Civic API · "
               "unitedstates/congress-legislators · Wikidata · Google Gemini AI")
