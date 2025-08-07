# … cabecera idéntica …

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ──── Datos de ejemplo (sin cambios) ────
RAW_EVENTS = [
    ("ProveedorNuevo", "DIOR",            "CHILE LUX",  "06-ago-25"),
    ("ProveedorNuevo", "Givenchy",        "CHILE LUX",  "05-ago-25"),
    ("ProveedorNuevo", "Kenzo",           "CHILE LUX",  "05-ago-25"),
    ("ProveedorNuevo", "DIOR",            "PANAMA",     "29-ago-25"),
    ("ProveedorNuevo", "VICTORIA SECRET", "PANAMA",     "25-ago-25"),
    ("ProveedorNuevo", "COTY",            "COSTA RICA", "11-ago-25"),
    ("ProveedorNuevo", "PUIG",            "PANAMA",     "08-ago-25"),
    ("ProveedorNuevo", "MAC",             "PANAMA",     "15-ago-25"),
    ("ProveedorNuevo", "CHANEL",          "PANAMA",     "08-ago-25"),
    ("ProveedorNuevo", "CHANEL",          "COLOMBIA",   "06-ago-25"),
    ("ProveedorNuevo", "CHANEL",          "COSTA RICA", "08-ago-25"),
    ("ProveedorNuevo", "DIOR",            "COLOMBIA",   "06-ago-25"),
    ("ProveedorNuevo", "VICTORIA SECRET", "COLOMBIA",   "25-ago-25"),
    ("ProveedorNuevo", "JEANNE ARTHES",   "COLOMBIA",   "15-ago-25"),
    ("ProveedorNuevo", "SWAROVSKI",       "COLOMBIA",   "08-ago-25"),
    ("ProveedorNuevo", "CLARINS",         "COSTA RICA", "15-ago-25"),
    ("ProveedorNuevo", "LOCCITANE",       "COSTA RICA", "11-ago-25"),
    ("ProveedorNuevo", "CARTIER",         "COSTA RICA", "15-ago-25"),
    ("ProveedorNuevo", "RISE",            "PANAMA",     "11-ago-25"),
]

# … resto del archivo igual hasta la sección ICS …

# ───────── Generar ICS ─────────
@app.get("/api/ics")
def api_ics(country: str, user: str = Depends(_require_user)):
    cal = Calendar()
    cal.add('prodid', '-//Saint Honoré Pedidos//es')   # ← Etiqueta PRODiD actualizada
    cal.add('version', '2.0')

    for e in load_events():
        if e["pais"] != country:
            continue
        ev = Event()
        ev.add('summary', f"{e['marca']} – PEDIDO")
        ev.add('dtstart', e["fecha"])
        ev.add('dtend', e["fecha"] + timedelta(hours=1))
        ev.add('dtstamp', datetime.utcnow())

        # alarma 1 día antes
        alarm = Alarm()
        alarm.add('trigger', timedelta(days=-1))
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'Recordatorio: pedido {e["marca"]}')
        ev.add_component(alarm)

        cal.add_component(ev)

    buf = io.BytesIO(cal.to_ical())
    headers = {
        'Cont
