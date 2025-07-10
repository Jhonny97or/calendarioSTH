# api/index.py

import os, io
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature
from datetime import datetime, timedelta
from functools import lru_cache
from icalendar import Calendar, Event, Alarm

# ─────────── Rutas base ───────────
# Este archivo está en <proyecto>/api/index.py
REPO_ROOT     = Path(__file__).resolve().parent.parent.parent
STATIC_DIR    = REPO_ROOT / "static"
TEMPLATES_DIR = REPO_ROOT / "templates"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ───── Credenciales demo ─────
CREDENTIALS = {"brand1": "brand1"}  # ajusta según necesites

# ──── Datos de ejemplo ────
RAW_EVENTS = [
    # ——— Proveedor 1 (CHANEL, CLARINS, …) ———
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "30-ene-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "28-feb-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "03-abr-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "06-may-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "05-jun-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "04-jul-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "06-ago-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "04-sep-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "03-oct-25"),
    ("Proveedor1", "CHANEL",  "COLOMBIA",   "31-oct-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "30-ene-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "28-feb-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "05-abr-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "08-may-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "07-jun-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "06-jul-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "08-ago-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "06-sep-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "05-oct-25"),
    ("Proveedor1", "CHANEL",  "COSTA RICA", "07-nov-25"),
    # CLARINS
    ("Proveedor1", "CLARINS", "COLOMBIA",   ""),
    ("Proveedor1", "CLARINS", "COLOMBIA",   ""),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-mar-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-abr-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-may-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-jun-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-jul-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-ago-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-sep-25"),
    ("Proveedor1", "CLARINS", "COLOMBIA",   "15-oct-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", ""),
    ("Proveedor1", "CLARINS", "COSTA RICA", ""),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-mar-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-abr-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-may-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-jun-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-jul-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-ago-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-sep-25"),
    ("Proveedor1", "CLARINS", "COSTA RICA", "15-oct-25"),
    # JA / JA SKILL
    ("Proveedor1", "JA",      "COLOMBIA",   "16-feb-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   ""),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-abr-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-may-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-jun-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-jul-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-ago-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-sep-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-oct-25"),
    ("Proveedor1", "JA",      "COLOMBIA",   "15-nov-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","05-feb-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA",""),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-abr-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-may-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-jun-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-jul-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-ago-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-sep-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-oct-25"),
    ("Proveedor1", "JA / SKILL","COSTA RICA","15-nov-25"),
    # CHANEL DFA/NORA/IMAS — etc.  (resto igual)
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-feb-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-mar-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-abr-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-may-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-jun-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-jul-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-ago-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-sep-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "10-oct-25"),
    ("Proveedor1", "CHANEL",  "DFA/ NORA / IMAS", "31-oct-25"),
    # HÉRMES CR + DFA/NORA/IMAS
    ("Proveedor1", "HÉRMES",  "COSTA RICA", ""),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", ""),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "31-mar-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "30-abr-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "30-may-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "30-jun-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "31-jul-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "31-ago-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "31-oct-25"),
    ("Proveedor1", "HÉRMES",  "COSTA RICA", "30-nov-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", ""),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", ""),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "31-mar-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "30-abr-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "30-may-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "30-jun-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "31-jul-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "31-ago-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "31-oct-25"),
    ("Proveedor1", "HÉRMES",  "DFA/ NORA / IMAS", "30-nov-25"),
    # Otros
    ("Proveedor1", "PUPA",    "COSTA RICA", "15-jun-25"),
    ("Proveedor1", "PUPA",    "COSTA RICA", "15-sep-25"),
    ("Proveedor1", "CARTIER", "COSTA RICA", "15-may-25"),
    ("Proveedor1", "CARTIER", "COSTA RICA", "15-ago-25"),
    ("Proveedor1", "ICONIC",  "COSTA RICA", "15-jun-25"),

    # ——— Proveedor 2 (DIOR + LFB) ———
    ("Proveedor2", "DIOR", "COSTA RICA", "06-jun-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-jul-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-ago-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-sep-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-oct-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-nov-25"),
    ("Proveedor2", "DIOR", "COSTA RICA", "06-dic-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-jun-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-jul-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-ago-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-sep-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-oct-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-nov-25"),
    ("Proveedor2", "DIOR", "COLOMBIA", "06-dic-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-jun-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-jul-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-ago-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-sep-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-oct-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-nov-25"),
    ("Proveedor2", "DIOR", "CHILE", "06-dic-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-jun-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-jul-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-ago-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-sep-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-oct-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-nov-25"),
    ("Proveedor2", "LFB",  "CHILE", "02-dic-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-jun-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-jul-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-ago-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-sep-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-oct-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-nov-25"),
    ("Proveedor2", "LFB",  "COSTA RICA", "02-dic-25"),

    # ——— Proveedor 3 (Panamá) ———
    ("Proveedor3", "ACTIUM",                              "PANAMA", "06-jul-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-jul-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-jul-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-jul-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-jul-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-jul-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-jul-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-jul-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-jul-25"),
    ("Proveedor3", "ACTIUM",                              "PANAMA", "06-ago-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-ago-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-ago-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-ago-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-ago-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-ago-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-ago-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-ago-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-ago-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-sep-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-sep-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-sep-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-sep-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-sep-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-sep-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-sep-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-sep-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-oct-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-oct-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-oct-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-oct-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-oct-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-oct-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-oct-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-oct-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-nov-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-nov-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-nov-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-nov-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-nov-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-nov-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-nov-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-nov-25"),
    ("Proveedor3", "AGENCIAS FEDURO",                     "PANAMA", "10-dic-25"),
    ("Proveedor3", "BEAUTE PRESTIGE INTERNATIONAL SAS",   "PANAMA", "06-dic-25"),
    ("Proveedor3", "BELUXE LATAM SA",                     "PANAMA", "06-dic-25"),
    ("Proveedor3", "DOLCE & GABBANA BEAUTY USA INC.",     "PANAMA", "06-dic-25"),
    ("Proveedor3", "ESSENCE CORPORATION",                 "PANAMA", "06-dic-25"),
    ("Proveedor3", "ESTEE LAUDER AG LACHEN",              "PANAMA", "06-dic-25"),
    ("Proveedor3", "MLL BRAND IMPORT LLC",                "PANAMA", "06-dic-25"),
    ("Proveedor3", "SHISEIDO TRAVEL RETAIL AMERICAS",     "PANAMA", "06-dic-25"),
]


SPANISH_MONTHS = {
    "ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,
    "jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12,
}

def parse_spanish_date(s: str) -> datetime:
    d, m, yy = s.split("-")
    return datetime(2000 + int(yy), SPANISH_MONTHS[m.lower()], int(d))

@lru_cache(maxsize=1)
def load_events():
    return [
        {"marca": m, "pais": c, "fecha": parse_spanish_date(f)}
        for _, m, c, f in RAW_EVENTS
        if f
    ]

def _get_user(req: Request):
    tok = req.cookies.get("session")
    if not tok:
        return None
    try:
        return signer.unsign(tok).decode()
    except BadSignature:
        return None

def _require_user(req: Request):
    if not _get_user(req):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return _get_user(req)

# ───── Login / Logout ─────
@app.get("/login", response_class=HTMLResponse)
def login_get(req: Request):
    if _get_user(req):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": req, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(req: Request,
               username: str = Form(...),
               password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html",
                                          {"request": req, "error": "Credenciales incorrectas"})
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session",
                    signer.sign(username.encode()).decode(),
                    httponly=True,
                    max_age=60 * 60 * 24 * 30,
                    path="/",
                    samesite="lax")
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session", path="/")
    return resp

# ───────── Home ─────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse("calendar.html",
                                      {"request": request, "user": user})

# ───────── API JSON ─────────
@app.get("/api/countries")
def api_countries(user: str = Depends(_require_user)):
    return JSONResponse(sorted({e["pais"] for e in load_events()}))

@app.get("/api/events")
def api_events(country: str, user: str = Depends(_require_user)):
    return JSONResponse([
        {
            "title": f"{e['marca']} – PEDIDO",
            "start": e["fecha"].date().isoformat(),
            "allDay": True,
            "backgroundColor": "#f58220",
            "borderColor": "#f58220",
        }
        for e in load_events() if e["pais"] == country
    ])

# ───────── Generar ICS ─────────
@app.get("/api/ics")
def api_ics(country: str, user: str = Depends(_require_user)):
    cal = Calendar()
    cal.add('prodid', '-//Saint Honore//es')
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
        'Content-Disposition': f'attachment; filename="pedidos_{country}.ics"'
    }
    return StreamingResponse(buf, media_type='text/calendar', headers=headers)
