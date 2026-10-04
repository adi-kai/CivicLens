"""Hand-verified 2026 general election deadlines, by state.

Every date here was checked against the state's official election website on the date
in `verified` — the URL on each item is the page that states it. A wrong deadline can
cost someone their vote, so:
  - Re-verify every date (and bump `verified`) before each election.
  - Only add a state after checking each item against its official site. Never compute
    a date from a rule unless the official page states the date or the rule plainly.
  - Leave an item out rather than guess (e.g. Tennessee's mail postmark date isn't
    stated anywhere official, so only the overall deadline is listed).

Items: `name` is translated through t(); `date` (or `start`/`end`) are ISO dates, so the
tab can format them in either language and mark deadlines that have passed; `time` is
English and converted for Spanish by format_date(); `note` holds both languages.
"""

NC_REG   = "https://www.ncsbe.gov/news/press-releases/2026/10/02/regular-voter-registration-deadline-approaching-2026-general-election"
NC_EARLY = "https://www.ncsbe.gov/voting/vote-early-person"
NC_MAIL  = "https://www.ncsbe.gov/voting/vote-mail/detailed-instructions-voting-mail"

SC_REG    = "https://scvotes.gov/get-registered-for-statewide-general-election-before-october-4-deadline/"
SC_EARLY  = "https://scvotes.gov/voters/early-voting/"
SC_ABS    = "https://scvotes.gov/voters/absentee-voting/"
SC_PREP   = "https://scvotes.gov/voters/2026prep/"

VA_DATES  = "https://www.elections.virginia.gov/casting-a-ballot/calendars-schedules/upcoming-elections.html"
VA_NEWS   = "https://www.elections.virginia.gov/news-releases/early-voting-for-2026-november-general-election-begins-sept-18-1.html"
VA_ABS    = "https://www.elections.virginia.gov/casting-a-ballot/early-absentee/"

TN_CAL    = "https://sos.tn.gov/elections/calendar"
TN_NEWS   = "https://sos.tn.gov/newsroom/press-releases/secretary-of-state-tre-hargett-encourages-eligible-tennesseans-to-register"
TN_ABS    = "https://sos.tn.gov/elections/guides/guide-to-absentee-voting"

GA_DATES  = "https://sos.ga.gov/november-3-2026-general-election"
# The official absentee guide (linked from sos.ga.gov's voting how-to page) is where the
# received-by-close-of-polls rule is stated
GA_ABS    = "https://sos.ga.gov/sites/default/files/forms/Absentee_Voting_In_Georgia_Rev_3-30-22.pdf"

STATE_DEADLINES = {
    "NC": {
        "source": "NC State Board of Elections", "site": "ncsbe.gov", "verified": "2026-10-03",
        "items": [
            {"name": "Voter Registration Deadline", "date": "2026-10-09", "time": "5 p.m.", "url": NC_REG,
             "note": {"en": "Deadline to register to vote by mail or on Election Day.",
                      "es": "Fecha límite para inscribirte y votar por correo o el Día de las Elecciones."}},
            {"name": "Same-Day Registration (Early Voting)", "start": "2026-10-15", "end": "2026-10-31", "url": NC_EARLY,
             "note": {"en": "Missed the deadline? Register and vote at any early voting site in your county. Not available for most voters on Election Day.",
                      "es": "¿Se te pasó la fecha? Inscríbete y vota en cualquier centro de votación anticipada de tu condado. No está disponible para la mayoría de los votantes el Día de las Elecciones."}},
            {"name": "Early Voting Begins", "date": "2026-10-15", "url": NC_EARLY,
             "note": {"en": "No excuse needed in NC.", "es": "En Carolina del Norte no necesitas una razón."}},
            {"name": "Early Voting Ends", "date": "2026-10-31", "time": "3 p.m.", "url": NC_EARLY,
             "note": {"en": "Last chance to vote early.", "es": "Última oportunidad para votar por anticipado."}},
            {"name": "Absentee Ballot Request Deadline", "date": "2026-10-20", "time": "5 p.m.", "url": NC_MAIL,
             "note": {"en": "Your county board of elections must receive the request by this time. (Military and overseas voters: 5 p.m. November 2.)",
                      "es": "La junta electoral de tu condado debe recibir la solicitud a esta hora. (Votantes militares y en el extranjero: 5 p. m. del 2 de noviembre)."}},
            {"name": "Absentee Ballot Return Deadline", "date": "2026-11-03", "time": "7:30 p.m.", "url": NC_MAIL,
             "note": {"en": "Your county board of elections must <strong>receive</strong> your ballot by this time — a postmark by Election Day is no longer enough.",
                      "es": "La junta electoral de tu condado debe <strong>recibir</strong> tu boleta a esta hora; ya no basta con el matasellos del Día de las Elecciones."}},
        ],
    },
    "SC": {
        "source": "SC State Election Commission", "site": "scvotes.gov", "verified": "2026-10-03",
        "items": [
            {"name": "Voter Registration Deadline — In Person", "date": "2026-10-02", "time": "5 p.m.", "url": SC_REG,
             "note": {"en": "Most county voter registration offices close at 5 p.m. for in-office registration. Some counties may hold weekend hours.",
                      "es": "La mayoría de las oficinas de inscripción de los condados cierran a las 5 p. m. Algunos condados pueden abrir el fin de semana."}},
            {"name": "Voter Registration Deadline — Online, Fax, or Email", "date": "2026-10-04", "time": "11:59 p.m.", "url": SC_REG,
             "note": {"en": "Your registration must be received by this time.",
                      "es": "Tu inscripción debe recibirse a más tardar a esta hora."}},
            {"name": "Voter Registration Deadline — By Mail", "date": "2026-10-05", "url": SC_REG,
             "note": {"en": "Your form must be postmarked by this date.",
                      "es": "Tu formulario debe tener matasellos de esta fecha o antes."}},
            {"name": "Early Voting", "start": "2026-10-19", "end": "2026-10-31", "url": SC_EARLY,
             "note": {"en": "Early voting centers are open 8:30 a.m.–6 p.m., Monday–Saturday. Closed Sunday, October 25.",
                      "es": "Los centros de votación anticipada abren de 8:30 a. m. a 6 p. m., de lunes a sábado. Cerrados el domingo 25 de octubre."}},
            {"name": "Absentee Ballot Request Deadline", "date": "2026-10-23", "time": "5 p.m.", "url": SC_ABS,
             "note": {"en": "Your application must be returned by 5 p.m. on the 11th day before the election.",
                      "es": "Debes entregar tu solicitud a más tardar a las 5 p. m. del undécimo día antes de la elección."}},
            {"name": "Absentee Ballot Return Deadline", "date": "2026-11-03", "time": "7 p.m.", "url": SC_PREP,
             "note": {"en": "Your county voter registration office must <strong>receive</strong> your ballot by this time. Mail it at least a week before Election Day.",
                      "es": "La oficina de inscripción de tu condado debe <strong>recibir</strong> tu boleta a esta hora. Envíala por correo al menos una semana antes del Día de las Elecciones."}},
        ],
    },
    "VA": {
        "source": "Virginia Department of Elections", "site": "elections.virginia.gov", "verified": "2026-10-03",
        "items": [
            {"name": "Voter Registration Deadline", "date": "2026-10-23", "url": VA_DATES,
             "note": {"en": "Online, by mail (postmarked by this date), or in person (registrar offices close at 5 p.m.).",
                      "es": "En línea, por correo (con matasellos de esta fecha o antes) o en persona (las oficinas del registrador cierran a las 5 p. m.)."}},
            {"name": "Same-Day Registration (Provisional Ballot)", "start": "2026-10-24", "end": "2026-11-03", "url": VA_NEWS,
             "note": {"en": "After the deadline, you can register and vote at the same time with a provisional ballot — at your registrar's office during early voting, or at your own polling place on Election Day.",
                      "es": "Después de la fecha límite, puedes inscribirte y votar al mismo tiempo con una boleta provisional: en la oficina de tu registrador durante la votación anticipada o en tu lugar de votación el Día de las Elecciones."}},
            {"name": "Early Voting", "start": "2026-09-18", "end": "2026-10-31", "url": VA_DATES,
             "note": {"en": "Ends at 5 p.m. on Saturday, October 31. Locations and hours vary by locality — contact your local registrar.",
                      "es": "Termina a las 5 p. m. del sábado 31 de octubre. Los lugares y horarios varían según la localidad; comunícate con tu registrador local."}},
            {"name": "Absentee Ballot Request Deadline", "date": "2026-10-23", "time": "5 p.m.", "url": VA_DATES,
             "note": {"en": "Last day to request a ballot by mail or online.",
                      "es": "Último día para solicitar una boleta por correo o en línea."}},
            {"name": "Absentee Ballot Return — In Person or Drop-Off", "date": "2026-11-03", "time": "7 p.m.", "url": VA_ABS,
             "note": {"en": "Return it to your general registrar's office or a drop-off location.",
                      "es": "Entrégala en la oficina de tu registrador general o en un lugar de entrega."}},
            {"name": "Absentee Ballot Return — By Mail", "date": "2026-11-06", "time": "noon", "url": VA_ABS,
             "note": {"en": "Must be postmarked on or before Election Day (November 3) <strong>and</strong> received by noon on November 6.",
                      "es": "Debe tener matasellos del Día de las Elecciones (3 de noviembre) o antes <strong>y</strong> recibirse antes del mediodía del 6 de noviembre."}},
        ],
    },
    "TN": {
        "source": "Tennessee Secretary of State", "site": "sos.tn.gov", "verified": "2026-10-03",
        "items": [
            {"name": "Voter Registration Deadline", "date": "2026-10-05", "time": "11:59 p.m.", "url": TN_NEWS,
             "note": {"en": "The same deadline applies to online registration.",
                      "es": "La misma fecha límite aplica para la inscripción en línea."}},
            {"name": "Early Voting", "start": "2026-10-14", "end": "2026-10-29", "url": TN_CAL,
             "note": {"en": "Hours and locations are set by your county election commission.",
                      "es": "Los horarios y lugares los fija la comisión electoral de tu condado."}},
            {"name": "Absentee Ballot Request Deadline", "date": "2026-10-24", "url": TN_ABS,
             "note": {"en": "Your county election commission must receive your request by this date. Tennessee only allows voting by mail for certain reasons — for example, if you're 60 or older.",
                      "es": "La comisión electoral de tu condado debe recibir tu solicitud a más tardar en esta fecha. Tennessee solo permite votar por correo por ciertas razones, por ejemplo, si tienes 60 años o más."}},
            {"name": "Absentee Ballot Return Deadline", "date": "2026-11-03", "url": TN_ABS,
             "note": {"en": "Your county election commission must <strong>receive</strong> your ballot by the close of polls. Return it by mail only — hand delivery isn't allowed.",
                      "es": "La comisión electoral de tu condado debe <strong>recibir</strong> tu boleta antes del cierre de las urnas. Devuélvela solo por correo; no se permite entregarla en persona."}},
        ],
    },
    "GA": {
        "source": "Georgia Secretary of State", "site": "sos.ga.gov", "verified": "2026-10-03",
        "items": [
            {"name": "Voter Registration Deadline", "date": "2026-10-05", "url": GA_DATES,
             "note": {"en": "Last day to register to vote in the general election.",
                      "es": "Último día para inscribirte y votar en la elección general."}},
            {"name": "Early Voting", "start": "2026-10-13", "end": "2026-10-30", "url": GA_DATES,
             "note": {"en": "Includes Saturdays; some counties also offer Sunday voting. Times and locations are on your county's My Voter Page.",
                      "es": "Incluye los sábados; algunos condados también abren los domingos. Los horarios y lugares aparecen en la página My Voter Page de tu condado."}},
            {"name": "Absentee Ballot Request Deadline", "date": "2026-10-23", "url": GA_DATES,
             "note": {"en": "Your election office must receive your application by this date. Missed it? You can still vote in person.",
                      "es": "Tu oficina electoral debe recibir tu solicitud a más tardar en esta fecha. ¿Se te pasó? Todavía puedes votar en persona."}},
            {"name": "Absentee Ballot Return Deadline", "date": "2026-11-03", "time": "7 p.m.", "url": GA_ABS,
             "note": {"en": "Your county registrar must <strong>receive</strong> your ballot by the close of polls. Return it by mail or in a ballot drop box.",
                      "es": "El registrador de tu condado debe <strong>recibir</strong> tu boleta antes del cierre de las urnas. Devuélvela por correo o en un buzón de boletas."}},
        ],
    },
}
