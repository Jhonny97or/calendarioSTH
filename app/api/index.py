import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

from datetime import date
from functools import lru_cache

# ── Ajuste de rutas base ───────────────────────────────────────────────────
# __file__ apunta a .../app/api/index.py
REPO_ROOT     = Path(__file__).resolve().parent.parent.parent  # …/ (var/task)
STATIC_DIR    = REPO_ROOT / "static"
TEMPLATES_DIR = REPO_ROOT / "templates"

# ── App y mounts ─────────────────────────────────────────────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ── Credenciales demo ─────────────────────────────────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

# ── Datos manuales (Marca, País, Fecha) ────────────────────────────────────
RAW_EVENTS = [
    ("CHANEL",     "COLOMBIA",    "30-ene-25"),
    ("CHANEL",     "COLOMBIA",    "28-feb-25"),
    ("CHANEL",     "COLOMBIA",    "03-abr-25"),
    ("CHANEL",     "COLOMBIA",    "06-may-25"),
    ("CHANEL",     "COLOMBIA",    "05-jun-25"),
    ("CHANEL",     "COLOMBIA",    "04-jul-25"),
    ("CHANEL",     "COLOMBIA",    "06-ago-25"),
    ("CHANEL",     "COLOMBIA",    "04-sep-25"),
    ("CHANEL",     "COLOMBIA",    "03-oct-25"),
    ("CHANEL",     "COLOMBIA",    "31-oct-25"),
    ("CHANEL",     "COSTA RICA",  "30-ene-25"),
    ("CHANEL",     "COSTA RICA",  "28-feb-25"),
    ("CHANEL",     "COSTA RICA",  "05-abr-25"),
    ("CHANEL",     "COSTA RICA",  "08-may-25"),
    ("CHANEL",     "COSTA RICA",  "07-jun-25"),
    ("CHANEL",     "COSTA RICA",  "06-jul-25"),
    ("CHANEL",     "COSTA RICA",  "08-ago-25"),
    ("CHANEL",     "COSTA RICA",  "06-sep-25"),
    ("CHANEL",     "COSTA RICA",  "05-oct-25"),
    ("CHANEL",     "COSTA RICA",  "07-nov-25"),
    ("CLARINS",    "COLOMBIA",    ""),             # sin fecha
    ("CLARINS",    "COLOMBIA",    ""),             # sin fecha
    ("CLARINS",    "COLOMBIA",    "15-mar-25"),
    ("CLARINS",    "COLOMBIA",    "15-abr-25"),
    ("CLARINS",    "COLOMBIA",    "15-may-25"),
    ("CLARINS",    "COLOMBIA",    "15-jun-25"),
    ("CLARINS",    "COLOMBIA",    "15-jul-25"),
    ("CLARINS",    "COLOMBIA",    "15-ago-25"),
    ("CLARINS",    "COLOMBIA",    "15-sep-25"),
    ("CLARINS",    "COLOMBIA",    "15-oct-25"),
    ("CLARINS",    "COSTA RICA",  ""),             # sin fecha
    ("CLARINS",    "COSTA RICA",  ""),             # sin fecha
    ("CLARINS",    "COSTA RICA",  "15-mar-25"),
    ("CLARINS",    "COSTA RICA",  "15-abr-25"),
    ("CLARINS",    "COSTA RICA",  "15-may-25"),
    ("CLARINS",    "COSTA RICA",  "15-jun-25"),
    ("CLARINS",    "COSTA RICA",  "15-jul-25"),
    ("CLARINS",    "COSTA RICA",  "15-ago-25"),
    ("CLARINS",    "COSTA RICA",  "15-sep-25"),
    ("CLARINS",    "COSTA RICA",  "15-oct-25"),
    ("JA",         "COLOMBIA",    "16-feb-25"),
    ("JA",         "COLOMBIA",    ""),             # sin fecha
    ("JA",         "COLOMBIA",    "15-abr-25"),
    ("JA",         "COLOMBIA",    "15-may-25"),
    ("JA",         "COLOMBIA",    "15-jun-25"),
    ("JA",         "COLOMBIA",    "15-jul-25"),
    ("JA",         "COLOMBIA",    "15-ago-25"),
    ("JA",         "COLOMBIA",    "15-sep-25"),
    ("JA",         "COLOMBIA",    "15-oct-25"),
    ("JA",         "COLOMBIA",    "15-nov-25"),
    ("JA / SKILL", "COSTA RICA",  "05-feb-25"),
    ("JA / SKILL", "COSTA RICA",  ""),             # sin fecha
    ("JA / SKILL", "COSTA RICA",  "15-abr-25"),
    ("JA / SKILL", "COSTA RICA",  "15-may-25"),
    ("JA / SKILL", "COSTA RICA",  "15-jun-25"),
    ("JA / SKILL", "COSTA RICA",  "15-jul-25"),
    ("JA / SKILL", "COSTA RICA",  "15-ago-25"),
    ("JA / SKILL", "COSTA RICA",  "15-sep-25"),
    ("JA / SKILL", "COSTA RICA",  "15-oct-25"),
    ("JA / SKILL", "COSTA RICA",  "15-nov-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-feb-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-mar-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-abr-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-may-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-jun-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-jul-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-ago-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-sep-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "10-oct-25"),
    ("CHANEL",     "DFA/ NORA / IMAS", "31-oct-25"),
    ("HÉRMES",     "COSTA RICA",  ""),             # sin fecha
    ("HÉRMES",     "COSTA RICA",  ""),             # sin fecha
    ("HÉRMES",     "COSTA RICA",  "31-mar-25"),
    ("HÉRMES",     "COSTA RICA",  "30-abr-25"),
    ("HÉRMES",     "COSTA RICA",  "30-may-25"),
    ("HÉRMES",     "COSTA RICA",  "30-jun-25"),
    ("HÉRMES",     "COSTA RICA",  "31-jul-25"),
    ("HÉRMES",     "COSTA RICA",  "31-ago-25"),
    ("HÉRMES",     "COSTA RICA",  "31-oct-25"),
    ("HÉRMES",     "COSTA RICA",  "30-nov-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS",""),        # sin fecha
    ("HÉRMES",     "DFA/ NORA / IMAS",""),        # sin fecha
    ("HÉRMES",     "DFA/ NORA / IMAS","31-mar-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","30-abr-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","30-may-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","30-jun-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","31-jul-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","31-ago-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","31-oct-25"),
    ("HÉRMES",     "DFA/ NORA / IMAS","30-nov-25"),
    ("PUPA",       "COSTA RICA",  "15-jun-25"),
    ("PUPA",       "COSTA RICA",  "15-sep-25"),
    ("CARTIER",    "COSTA RICA",  "15-may-25"),
    ("CARTIER",    "COSTA RICA",  "15-ago-25"),
    ("ICONIC",     "COSTA RICA",  "15-jun-25"),
]

# ── Parsing de fechas españolas ─────────────────────────────────────────────
SPANISH_MONTHS = {
    'ene':1,'feb':2,'mar':3,'abr':4,
    'may':5,'jun':6,'jul':7,'ago':8,
    'sep':9,'oct':10,'nov':11,'dic':12
}

def parse_spanish_date(s: str) -> str:
    d, m, yy = s.split('-')
    return date(2000 + int(yy), SPANISH_MONTHS[m.lower()], int(d)).isoformat()

# ── Carga cacheada de eventos ───────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_events_manual():
    evs = []
    for marca, pais, fecha_str in RAW_EVENTS:
        if not fecha_str:
            continue
        evs.append({
            "proveedor": "Proveedor1",
            "pais":      pais,
            "marca":     marca,
            "user":      "brand1",
            "fecha_iso": parse_spanish_date(fecha_str)
        })
    return evs

# ── Sesión / Auth ─────────────────────────────────────────────────────────
def _get_user(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        return signer.unsign(token).decode()
    except BadSignature:
        return None

def _require_user(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

# ── Rutas de autenticación ────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if _get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Credenciales incorrectas"
        })
    resp = RedirectResponse("/", 303)
    resp.set_cookie("session", signer.sign(username.encode()).decode(),
                    httponly=True, max_age=60*60*24*30,
                    path="/", samesite="lax")
    return resp

@app.get("/logout")
def logout():
    r = RedirectResponse("/login", 303)
    r.delete_cookie("session", path="/")
    return r

# ── Página principal ───────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse("calendar.html", {
        "request": request, "user": user
    })

# ── API JSON ───────────────────────────────────────────────────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(_require_user)):
    provs = { ev["proveedor"] for ev in load_events_manual() if ev["user"] == user }
    return JSONResponse(sorted(provs))

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(_require_user)):
    ctries = {
        ev["pais"]
        for ev in load_events_manual()
        if ev["proveedor"] == provider and ev["user"] == user
    }
    return JSONResponse(sorted(ctries))

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(_require_user)):
    datos = []
    for ev in load_events_manual():
        if (ev["proveedor"], ev["pais"], ev["user"]) == (provider, country, user):
            datos.append({
                "title":           f"{ev['marca']} – PEDIDO",
                "start":           ev["fecha_iso"],
                "allDay":          True,
                "backgroundColor": "#f58220",
                "borderColor":     "#f58220"
            })
    return JSONResponse(datos)

