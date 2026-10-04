"""Home: welcome text and section overview."""
import streamlit as st

from civiclens.i18n import pick, t

WELCOME = {
    "en": """
Welcome! CivicLens helps **first-time and new voters** across the United States navigate every part of the civic process.

| Section | What it does |
|---|---|
| 📍 **Polling Finder** | Locate your polling place by address — any U.S. state |
| 📅 **Deadlines** | Election Day + your state's registration & voting deadlines |
| 🏛️ **My Representatives** | Every rep who represents you — state and federal |
| 🗺️ **Rep Map** | Interactive district map for any state, colored by party |
| 📋 **Bill Tracker** | Browse and search active legislation in any state |
| 🔍 **District Compare** | Compare reps for two addresses side by side — same state or different states |
| 🗳️ **Candidates** | Live 2026 candidate research with policy positions — any state |

**Get started →** pick any section on the left and enter your address. You only need to type it once.
""",
    "es": """
¡Te damos la bienvenida! CivicLens ayuda a **votantes nuevos y primerizos** de todo Estados Unidos a entender cada parte del proceso cívico.

| Sección | Qué hace |
|---|---|
| 📍 **Buscar lugar de votación** | Encuentra tu lugar de votación con tu dirección, en cualquier estado |
| 📅 **Fechas límite** | El Día de las Elecciones y las fechas de inscripción y votación de tu estado |
| 🏛️ **Mis representantes** | Todos los funcionarios electos que te representan, estatales y federales |
| 🗺️ **Mapa de distritos** | Mapa interactivo de los distritos de cualquier estado, coloreado por partido |
| 📋 **Proyectos de ley** | Explora y busca la legislación activa de cualquier estado |
| 🔍 **Comparar distritos** | Compara los representantes de dos direcciones, del mismo estado o de estados distintos |
| 🗳️ **Candidatos** | Información actualizada sobre los candidatos de 2026 y sus posturas, en cualquier estado |

**Para empezar →** elige una sección a la izquierda e ingresa tu dirección. Solo tienes que escribirla una vez.
""",
}


def render():
    st.title("🗳️ CivicLens")
    st.subheader(t("Your complete guide to voting and civic life — in all 50 states and DC"))
    st.markdown(pick(WELCOME))
    st.caption(t("Data: OpenStates · U.S. Census TIGERweb · Google Civic API · unitedstates/congress-legislators · Wikidata · Google Gemini AI"))
