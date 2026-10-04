"""English / Spanish interface text.

t("English text") returns the Spanish version when Spanish is selected, and the English
text otherwise — the English string is the lookup key, so code stays readable and a
missing translation falls back to English instead of breaking. Placeholders use
str.format: t("Hello {name}", name=x). tests/test_logic.py checks that every t("...")
literal in the code has a Spanish entry.

Data from outside sources (names, bill titles, AI search results' sources) stays as it
comes back; only the app's own text is translated.
"""
import datetime

import streamlit as st

LANGUAGES = {"en": "English", "es": "Español"}
LANG_KEY = "lang"


def current_lang() -> str:
    try:
        return st.session_state.get(LANG_KEY, "en")
    except Exception:
        return "en"


def translate(text: str, lang: str) -> str:
    return ES.get(text, text) if lang == "es" else text


def t(text: str, **kwargs) -> str:
    out = translate(text, current_lang())
    return out.format(**kwargs) if kwargs else out


def label_func(transform=lambda x: x):
    """A format_func for selectboxes and radios that translates option labels. It fixes
    the language when the widget is drawn, because Streamlit may call format_func later,
    outside the script run, where the session (and so the language) isn't available."""
    lang = current_lang()
    return lambda option: translate(transform(option), lang)


def pick(options: dict) -> str:
    """For longer passages kept as {"en": ..., "es": ...}."""
    return options.get(current_lang(), options["en"])


# ── Dates ────────────────────────────────────────────────────────────────────
_WEEKDAYS = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
             "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}
_MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December"],
           "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                  "septiembre", "octubre", "noviembre", "diciembre"]}


def format_date(iso: str, time: str = "", weekday: bool = True) -> str:
    """"2026-10-09", "5 p.m." → "5 p.m. Friday, October 9, 2026" /
    "5 p. m. del viernes 9 de octubre de 2026"."""
    d = datetime.date.fromisoformat(iso)
    lang = current_lang()
    wd = _WEEKDAYS[lang][d.weekday()]
    month = _MONTHS[lang][d.month - 1]
    if lang == "es":
        day = f"{wd} {d.day} de {month} de {d.year}" if weekday else f"{d.day} de {month} de {d.year}"
        if time:
            spanish_time = time.replace("p.m.", "p. m.").replace("a.m.", "a. m.").replace("noon", "mediodía")
            return f"{spanish_time} del {day}"
        return day
    day = f"{wd}, {month} {d.day}, {d.year}" if weekday else f"{month} {d.day}, {d.year}"
    return f"{time} {day}" if time else day


def format_range(start: str, end: str) -> str:
    """Two ISO dates in the same year → "October 15 – October 31, 2026" /
    "15 de octubre – 31 de octubre de 2026"."""
    a, b = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    lang = current_lang()
    ma, mb = _MONTHS[lang][a.month - 1], _MONTHS[lang][b.month - 1]
    if lang == "es":
        return f"{a.day} de {ma} – {b.day} de {mb} de {b.year}"
    return f"{ma} {a.day} – {mb} {b.day}, {b.year}"


# ── Spanish text ─────────────────────────────────────────────────────────────
# Gendered job titles are avoided: role labels name the body ("Senado estatal —
# Distrito 15") and offices use "(a)" forms, so no one's gender is assumed.
ES = {
    # Sidebar, navigation, footer
    "Navigate": "Navegar",
    "Color theme": "Tema de color",
    "🏠 Home": "🏠 Inicio",
    "📍 Polling Finder": "📍 Buscar lugar de votación",
    "📅 Deadlines": "📅 Fechas límite",
    "🏛️ My Representatives": "🏛️ Mis representantes",
    "🗺️ Rep Map": "🗺️ Mapa de distritos",
    "📋 Bill Tracker": "📋 Proyectos de ley",
    "🔍 District Compare": "🔍 Comparar distritos",
    "🗳️ Candidates": "🗳️ Candidatos",
    "Civic Teal": "Verde azulado cívico",
    "Pine & Marigold": "Pino y caléndula",
    "Plum & Mint": "Ciruela y menta",
    "Slate & Tangerine": "Pizarra y mandarina",
    "Midnight Violet": "Violeta medianoche",
    "Classic Civic": "Cívico clásico",
    "Red, White & Blue": "Rojo, blanco y azul",
    "Privacy Policy": "Política de privacidad",
    "Terms of Service": "Términos del servicio",
    "This document is available in English only.": "Este documento solo está disponible en inglés.",
    "The {title} is temporarily unavailable.": "{title}: no está disponible temporalmente.",
    "CivicLens is nonpartisan and not affiliated with any government agency.":
        "CivicLens es imparcial y no está afiliado a ninguna agencia del gobierno.",

    # Home
    "Your complete guide to voting and civic life — in all 50 states and DC":
        "Tu guía completa para votar y participar en la vida cívica, en los 50 estados y DC",
    "Data: OpenStates · U.S. Census TIGERweb · Google Civic API · unitedstates/congress-legislators · Wikidata · Google Gemini AI":
        "Datos: OpenStates · U.S. Census TIGERweb · Google Civic API · unitedstates/congress-legislators · Wikidata · Google Gemini AI",

    # Shared
    "Address:": "Dirección:",
    "Enter your address": "Ingresa tu dirección",
    "Please enter an address.": "Ingresa una dirección.",
    "Locating address…": "Ubicando la dirección…",
    "State": "Estado",
    "Unknown": "Desconocido",
    "Contact": "Contacto",
    "Photo of {name}": "Foto de {name}",
    "Source: {source}": "Fuente: {source}",

    # Offices, chambers, and role labels
    "Governor": "Gobernador(a)",
    "Mayor": "Alcalde(sa)",
    "U.S. Senate": "Senado de EE. UU.",
    "U.S. Senator": "Senado de EE. UU.",
    "U.S. Senators": "Senadores de EE. UU.",
    "U.S. Senator — {state}": "Senado de EE. UU. — {state}",
    "U.S. House": "Cámara de EE. UU.",
    "U.S. House — District {district}": "Cámara de Representantes de EE. UU. — Distrito {district}",
    "U.S. House At-Large": "Cámara de EE. UU. (distrito único)",
    "Delegate to the U.S. House": "Delegado(a) ante la Cámara de Representantes de EE. UU.",
    "D.C. Council": "Concejo de D.C.",
    "State Legislature": "Legislatura estatal",
    "State Senate": "Senado estatal",
    "State House": "Cámara estatal",
    "State Assembly": "Asamblea estatal",
    "State House of Delegates": "Cámara de Delegados estatal",
    "State House of Representatives": "Cámara de Representantes estatal",
    "State Senator": "Senado estatal",
    "State Representative": "Cámara de Representantes estatal",
    "State Assembly Member": "Asamblea estatal",
    "State Delegate": "Cámara de Delegados estatal",
    "{title} — District {district}": "{title} — Distrito {district}",
    "District {district}": "Distrito {district}",
    "{office} of {state}": "{office} de {state}",
    "🏛️ {office} of {state}": "🏛️ {office} de {state}",
    "U.S. Senators for {state}": "Senadores de EE. UU. por {state}",

    # Parties
    "Democratic": "Demócrata",
    "Democrat": "Demócrata",
    "Republican": "Republicano",
    "Independent": "Independiente",
    "Libertarian": "Libertario",
    "Green": "Verde",
    "Other / Unknown": "Otro / Desconocido",

    # States whose Spanish name differs (the rest are listed so the check stays simple)
    "Alabama": "Alabama", "Alaska": "Alaska", "Arizona": "Arizona", "Arkansas": "Arkansas",
    "California": "California", "Colorado": "Colorado", "Connecticut": "Connecticut",
    "Delaware": "Delaware", "District of Columbia": "Distrito de Columbia", "Florida": "Florida",
    "Georgia": "Georgia", "Hawaii": "Hawái", "Idaho": "Idaho", "Illinois": "Illinois",
    "Indiana": "Indiana", "Iowa": "Iowa", "Kansas": "Kansas", "Kentucky": "Kentucky",
    "Louisiana": "Luisiana", "Maine": "Maine", "Maryland": "Maryland",
    "Massachusetts": "Massachusetts", "Michigan": "Míchigan", "Minnesota": "Minnesota",
    "Mississippi": "Misisipi", "Missouri": "Misuri", "Montana": "Montana", "Nebraska": "Nebraska",
    "Nevada": "Nevada", "New Hampshire": "Nuevo Hampshire", "New Jersey": "Nueva Jersey",
    "New Mexico": "Nuevo México", "New York": "Nueva York", "North Carolina": "Carolina del Norte",
    "North Dakota": "Dakota del Norte", "Ohio": "Ohio", "Oklahoma": "Oklahoma", "Oregon": "Oregón",
    "Pennsylvania": "Pensilvania", "Rhode Island": "Rhode Island", "South Carolina": "Carolina del Sur",
    "South Dakota": "Dakota del Sur", "Tennessee": "Tennessee", "Texas": "Texas", "Utah": "Utah",
    "Vermont": "Vermont", "Virginia": "Virginia", "Washington": "Washington",
    "West Virginia": "Virginia Occidental", "Wisconsin": "Wisconsin", "Wyoming": "Wyoming",

    # Polling Finder
    "📍 Find Your Polling Place": "📍 Encuentra tu lugar de votación",
    "Works for any U.S. address — powered by the Google Civic Information API.":
        "Funciona con cualquier dirección de EE. UU., con datos de la API Google Civic Information.",
    "Enter your full address": "Ingresa tu dirección completa",
    "Search": "Buscar",
    "Looking up your polling place…": "Buscando tu lugar de votación…",
    "✅ Polling location found!": "✅ ¡Encontramos tu lugar de votación!",
    "Polling Location": "Lugar de votación",
    "🕐 Hours: {hours}": "🕐 Horario: {hours}",
    "Polling location not available right now — no active election. Use these resources:":
        "El lugar de votación no está disponible en este momento porque no hay una elección activa. Usa estos recursos:",
    "Voting Location Finder": "Buscador de lugares de votación",
    "Register to Vote": "Inscríbete para votar",
    "Absentee / Mail Voting Info": "Información sobre el voto por correo",
    "Ballot Information": "Información sobre la boleta",
    "🗳️ {state} Voting Resources": "🗳️ Recursos para votar en {state}",
    "🗳️ Voting Resources": "🗳️ Recursos para votar",
    "Register to Vote in {state} — Vote.gov": "Inscríbete para votar en {state} — Vote.gov",
    "Check Your Registration Status — Vote.org": "Verifica tu inscripción — Vote.org",
    "Find Your Polling Place — Vote.org": "Encuentra tu lugar de votación — Vote.org",
    "Absentee / Mail Voting Info — Vote.org": "Información sobre el voto por correo — Vote.org",
    "Your State Election Office — U.S. EAC Directory": "La oficina electoral de tu estado — Directorio de la EAC de EE. UU.",
    "Find Your Polling Place": "Encuentra tu lugar de votación",
    "Check Registration Status": "Verifica tu inscripción",
    "Absentee Ballot Info": "Información sobre la boleta por correo",
    "Check Registration & Find Your Polling Place": "Verifica tu inscripción y encuentra tu lugar de votación",
    "Request an Absentee Ballot": "Solicita una boleta por correo",

    # Deadlines
    "📅 Key Voting Deadlines — 2026": "📅 Fechas límite clave para votar — 2026",
    "Election Day itself is set federally — the same date nationwide. Registration and early-voting windows are set by each state, so enter your address below to see yours.":
        "El Día de las Elecciones lo fija la ley federal: es la misma fecha en todo el país. Los plazos de inscripción y de votación anticipada los fija cada estado, así que ingresa tu dirección abajo para ver los tuyos.",
    "Could not determine the state for that address — try adding your city and zip code.":
        "No se pudo determinar el estado de esa dirección; intenta agregar tu ciudad y código postal.",
    "Election Day": "Día de las Elecciones",
    "Polls open per your state and county's posted hours. Set by federal law — the same date nationwide.":
        "Las urnas abren según el horario publicado por tu estado y condado. Lo fija la ley federal: es la misma fecha en todo el país.",
    "Enter your address above to see registration and early-voting resources for your state.":
        "Ingresa tu dirección arriba para ver los recursos de inscripción y de votación anticipada de tu estado.",
    "Registration cutoffs, early-voting windows, and absentee deadlines for **{state}** vary and can change year to year, so we don't guess at exact dates here — use the official links below to get {state}'s current 2026 deadlines.":
        "Los plazos de inscripción, de votación anticipada y de voto por correo de **{state}** varían y pueden cambiar cada año, así que aquí no adivinamos fechas exactas: usa los enlaces oficiales de abajo para consultar las fechas límite actuales de {state} para 2026.",
    "{state} 2026 Deadlines": "Fechas límite de {state} para 2026",
    "Dates last verified against {site} on {date}.": "Fechas verificadas por última vez en {site} el {date}.",
    "🗳️ Official Resources": "🗳️ Recursos oficiales",
    "Always verify deadlines directly with {state}'s official election authority — rules can change.":
        "Confirma siempre las fechas límite directamente con la autoridad electoral oficial de {state}; las reglas pueden cambiar.",
    "Passed": "Ya pasó",
    "Today": "Hoy",
    "Tomorrow": "Mañana",
    "In {days} days": "En {days} días",
    "NC State Board of Elections": "Junta Electoral del Estado de Carolina del Norte",
    "SC State Election Commission": "Comisión Electoral del Estado de Carolina del Sur",
    "Virginia Department of Elections": "Departamento de Elecciones de Virginia",
    "Tennessee Secretary of State": "Secretaría de Estado de Tennessee",
    "Georgia Secretary of State": "Secretaría de Estado de Georgia",
    "Voter Registration Deadline": "Fecha límite de inscripción de votantes",
    "Voter Registration Deadline — In Person": "Fecha límite de inscripción — en persona",
    "Voter Registration Deadline — Online, Fax, or Email": "Fecha límite de inscripción — en línea, por fax o por correo electrónico",
    "Voter Registration Deadline — By Mail": "Fecha límite de inscripción — por correo",
    "Same-Day Registration (Early Voting)": "Inscripción el mismo día (votación anticipada)",
    "Same-Day Registration (Provisional Ballot)": "Inscripción el mismo día (boleta provisional)",
    "Early Voting": "Votación anticipada",
    "Early Voting Begins": "Comienza la votación anticipada",
    "Early Voting Ends": "Termina la votación anticipada",
    "Absentee Ballot Request Deadline": "Fecha límite para solicitar la boleta por correo",
    "Absentee Ballot Return Deadline": "Fecha límite para devolver la boleta por correo",
    "Absentee Ballot Return — In Person or Drop-Off": "Devolución de la boleta por correo — en persona o en un lugar de entrega",
    "Absentee Ballot Return — By Mail": "Devolución de la boleta por correo — por correo postal",

    # My Representatives
    "🏛️ Who Represents You?": "🏛️ ¿Quién te representa?",
    "Shows your state legislators AND your federal representatives in Congress — for any U.S. address.":
        "Muestra tus legisladores estatales Y tus representantes federales en el Congreso, para cualquier dirección de EE. UU.",
    "Find My Reps": "Buscar mis representantes",
    "Could not locate that address. Try adding your city and zip code.":
        "No se pudo encontrar esa dirección. Intenta agregar tu ciudad y código postal.",
    "Detected state: **{state}**": "Estado detectado: **{state}**",
    "Could not load the current {office} right now.": "No se pudo cargar el nombre del {office} actual en este momento.",
    "Loading your representatives…": "Cargando tus representantes…",
    "Could not load legislators for this address — OpenStates may be rate-limiting (10 requests/min). Wait a moment and search again.":
        "No se pudieron cargar los legisladores de esta dirección; es posible que OpenStates esté limitando las solicitudes (10 por minuto). Espera un momento y vuelve a buscar.",
    "🇺🇸 U.S. Senate": "🇺🇸 Senado de EE. UU.",
    "🇺🇸 U.S. House of Representatives": "🇺🇸 Cámara de Representantes de EE. UU.",

    # Rep Map
    "🗺️ District Map": "🗺️ Mapa de distritos",
    "Real district boundaries from the U.S. Census Bureau, colored by party. Click any district for rep details.":
        "Límites reales de los distritos de la Oficina del Censo de EE. UU., coloreados por partido. Haz clic en un distrito para ver a su representante.",
    "🔄 Clear map cache": "🔄 Borrar la caché del mapa",
    "Force re-fetch boundaries from Census — use if districts look wrong":
        "Vuelve a descargar los límites del Censo; úsalo si los distritos se ven mal",
    "Cache cleared — click Show Map to reload.": "Caché borrada; haz clic en Mostrar mapa para recargar.",
    "Enter your address (optional — pins your location and auto-selects the state below)":
        "Ingresa tu dirección (opcional: marca tu ubicación y selecciona el estado automáticamente)",
    "Auto-overridden if your address above resolves to a different state.":
        "Se reemplaza automáticamente si tu dirección corresponde a otro estado.",
    "Show district layer:": "Mostrar capa de distritos:",
    "Show Map": "Mostrar mapa",
    "Loading district data…": "Cargando datos de los distritos…",
    "📡 Geocoding address…": "📡 Ubicando la dirección…",
    "📍 Address resolved to **{state}** — using that state.": "📍 La dirección está en **{state}**; se usará ese estado.",
    "🗺️ Fetching Census district boundaries for {state}…": "🗺️ Descargando del Censo los límites de los distritos de {state}…",
    "👥 Loading representative data…": "👥 Cargando datos de los representantes…",
    "⚠️ Map loaded with errors — see below": "⚠️ El mapa se cargó con errores; mira abajo",
    "✅ Map data loaded!": "✅ ¡Datos del mapa cargados!",
    "⚠️ Could not load {label} district boundaries (TIGERweb layer {layer}). Last error: {err}. Click Show Map to retry. If this keeps happening, the Census TIGERweb layer IDs may have shifted again — check: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer":
        "⚠️ No se pudieron cargar los límites de {label} (capa {layer} de TIGERweb). Último error: {err}. Haz clic en Mostrar mapa para volver a intentarlo. Si sigue pasando, es posible que los identificadores de capa de TIGERweb del Censo hayan cambiado; revisa: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer",
    "⚠️ Could not load {chamber} representatives. Boundaries will show without rep names.":
        "⚠️ No se pudieron cargar los representantes de {chamber}. Los límites se mostrarán sin nombres.",
    "⚠️ Could not load U.S. Senators. The Senate overlay will show without names.":
        "⚠️ No se pudieron cargar los senadores de EE. UU. La capa del Senado se mostrará sin nombres.",
    "⚠️ Could not load the current {office} — {err}. The overlay will show without a name.":
        "⚠️ No se pudo cargar el nombre del {office} actual — {err}. La capa se mostrará sin nombre.",
    "Street map": "Mapa de calles",
    "No data": "Sin datos",
    "The District of Columbia has no voting U.S. Senators.": "El Distrito de Columbia no tiene senadores con voto en el Senado de EE. UU.",
    "Could not load this state's U.S. Senators right now.": "No se pudieron cargar los senadores de EE. UU. de este estado en este momento.",
    "📍 Your Address": "📍 Tu dirección",
    "You are here": "Estás aquí",
    "Party Key:": "Partidos:",
    "Click any district for rep details": "Haz clic en un distrito para ver a su representante",
    "District boundaries: U.S. Census Bureau TIGERweb · State legislators: OpenStates API · Congress: unitedstates/congress-legislators · Governors: Wikidata":
        "Límites de los distritos: TIGERweb de la Oficina del Censo de EE. UU. · Legisladores estatales: API de OpenStates · Congreso: unitedstates/congress-legislators · Gobernadores: Wikidata",

    # Bill Tracker
    "📋 State Bill Tracker": "📋 Proyectos de ley estatales",
    "Browse and search active state legislation for any state · Via OpenStates · Updated every 30 min":
        "Explora y busca la legislación estatal activa de cualquier estado · Vía OpenStates · Se actualiza cada 30 min",
    "Search by keyword": "Buscar por palabra clave",
    "e.g. school funding, gun safety, Medicaid": "p. ej., fondos escolares, seguridad de armas, Medicaid",
    "Chamber": "Cámara",
    "All": "Todas",
    "House": "Cámara de Representantes",
    "Senate": "Senado",
    "Search Bills": "Buscar proyectos de ley",
    "Loading bills…": "Cargando proyectos de ley…",
    "Could not load bills — {err}": "No se pudieron cargar los proyectos de ley — {err}",
    "No bills found. Try a different keyword or chamber.": "No se encontraron proyectos de ley. Prueba otra palabra clave u otra cámara.",
    "Showing {count} bills — sorted by most recent activity": "Mostrando {count} proyectos de ley, ordenados por actividad más reciente",
    "No title": "Sin título",
    "No recent action": "Sin acciones recientes",
    "{title} {name}{party}": "{name}{party} · {title}",
    "View full bill on OpenStates →": "Ver el proyecto completo en OpenStates →",
    "✨ Plain-English Summary": "✨ Resumen en lenguaje sencillo",
    "Summarizing…": "Resumiendo…",

    # District Compare
    "🔍 District Comparison": "🔍 Comparación de distritos",
    "Enter any two U.S. addresses — in the same state or different states — to compare their representatives side by side. Shared reps are highlighted in green.":
        "Ingresa dos direcciones de EE. UU., del mismo estado o de estados distintos, para comparar sus representantes lado a lado. Los representantes en común aparecen resaltados en verde.",
    "📍 Address 1": "📍 Dirección 1",
    "📍 Address 2": "📍 Dirección 2",
    "Compare Districts": "Comparar distritos",
    "Please enter both addresses.": "Ingresa ambas direcciones.",
    "Looking up representatives for both addresses…": "Buscando los representantes de ambas direcciones…",
    "Could not locate: **{address}**": "No se pudo encontrar: **{address}**",
    "{state} {label}": "{label} ({state})",
    "Shared": "En común",
    "No representatives found.": "No se encontraron representantes.",
    "✅ These addresses share **{count}** representative(s) — marked in green above.":
        "✅ Estas direcciones comparten **{count}** representante(s), marcados en verde arriba.",
    "These addresses are in different states ({state1} and {state2}), so they don't share any representatives — each state has its own legislators and U.S. Senators.":
        "Estas direcciones están en estados distintos ({state1} y {state2}), así que no comparten representantes: cada estado tiene sus propios legisladores y senadores de EE. UU.",
    "These addresses have entirely separate sets of representatives.": "Estas direcciones tienen representantes completamente distintos.",

    # Candidates
    "🗳️ 2026 Candidates": "🗳️ Candidatos 2026",
    "Powered by Google Gemini 2.5 Flash + Groq + Tavily + Google Search — free, nonpartisan, live from official campaign websites":
        "Con tecnología de Google Gemini 2.5 Flash + Groq + Tavily + Google Search: gratis, imparcial y actualizado a partir de los sitios oficiales de campaña",
    "Select Race": "Selecciona la contienda",
    "D.C. Council (enter ward below)": "Concejo de D.C. (ingresa el distrito abajo)",
    "U.S. House (at-large)": "Cámara de Representantes de EE. UU. (distrito único)",
    "U.S. House (enter district below)": "Cámara de Representantes de EE. UU. (ingresa el distrito abajo)",
    "Nebraska State Legislature (enter district below)": "Legislatura estatal de Nebraska (ingresa el distrito abajo)",
    "{state} {chamber} (enter district below)": "{chamber} de {state} (ingresa el distrito abajo)",
    "District": "distrito",
    "Ward": "distrito municipal (ward)",
    "{word} Number": "Número de {word}",
    "e.g. 14": "p. ej., 14",
    "Find Candidates & Positions": "Buscar candidatos y posturas",
    "Please enter a {word} number for this race type.": "Ingresa un número de {word} para este tipo de contienda.",
    "Searching for 2026 {state} {race} candidates — may take 15–30 seconds…":
        "Buscando candidatos de 2026 para {race} en {state}; puede tardar de 15 a 30 segundos…",
    "⚡ Gemini limit reached, switching to backup…": "⚡ Se alcanzó el límite de Gemini; cambiando al respaldo…",
    "⚡ Gemini unavailable, switching to backup…": "⚡ Gemini no está disponible; cambiando al respaldo…",
    "{state}'s election office": "la oficina electoral de {state}",
    "⚠️ AI-assisted research from public web sources. Always verify with official campaign sites and {link}. Results cached for 1 hour.":
        "⚠️ Investigación asistida por IA a partir de fuentes públicas en internet. Verifica siempre en los sitios oficiales de campaña y en {link}. Los resultados se guardan por 1 hora.",
}
