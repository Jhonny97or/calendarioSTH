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
REPO_ROOT     = Path(__file__).resolve().parent.parent.parent
STATIC_DIR    = REPO_ROOT / "static"
TEMPLATES_DIR = REPO_ROOT / "templates"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ───── Credenciales demo ─────
CREDENTIALS = {"brand1": "brand1"}  # ajusta según necesites

RAW_EVENTS = [ ("ProveedorNuevo", "DIOR", "CHILE LUX", "06-oct-25"), ("ProveedorNuevo", "Givenchy", "CHILE LUX", "02-oct-25"), ("ProveedorNuevo", "Kenzo", "CHILE LUX", "02-oct-25"), ("ProveedorNuevo", "Givenchy", "COSTA RICA", "06-oct-25"), ("ProveedorNuevo", "Kenzo", "COSTA RICA", "06-oct-25"), ("ProveedorNuevo", "Acqua di Parma", "CHILE LUX", "06-oct-25"), ("ProveedorNuevo", "Interparfums", "CHILE LUX", "10-oct-25"), ("ProveedorNuevo", "Sisley", "CHILE LUX", "13-oct-25"), ("ProveedorNuevo", "VICTORIA SECRET", "PANAMÁ", "24-oct-25"), ("ProveedorNuevo", "Bath & Body Works","PANAMÁ", "24-oct-25"), ("ProveedorNuevo", "COTY MASSTIGE", "PANAMÁ", "07-oct-25"), ("ProveedorNuevo", "MAC", "PANAMÁ", "15-oct-25"), ("ProveedorNuevo", "CHANEL", "PANAMÁ", "10-oct-25"), ("ProveedorNuevo", "CHANEL", "COLOMBIA", "06-oct-25"), ("ProveedorNuevo", "CHANEL", "COSTA RICA", "10-oct-25"), ("ProveedorNuevo", "DIOR", "COLOMBIA", "06-oct-25"), ("ProveedorNuevo", "VICTORIA SECRET", "COLOMBIA", "24-oct-25"), ("ProveedorNuevo", "MAC", "COLOMBIA", "15-oct-25"), ("ProveedorNuevo", "SWAROVSKI", "COLOMBIA", "02-oct-25"), ("ProveedorNuevo", "DIOR", "COSTA RICA", "31-oct-25"), ("ProveedorNuevo", "CLARINS", "COSTA RICA", "15-oct-25"), ("ProveedorNuevo", "SKILL", "COSTA RICA", "31-oct-25"), ("ProveedorNuevo", "JEANNE ARTHES", "COSTA RICA", "31-oct-25"), ("ProveedorNuevo", "RISE", "PANAMÁ", "02-oct-25"), ("ProveedorNuevo", "SWAROVSKI", "PERÚ", "02-oct-25"), ("ProveedorNuevo", "FENTY", "COLOMBIA", "06-oct-25"), ("ProveedorNuevo", "LOREAL", "COLOMBIA", "06-oct-25"), ]


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

# ───── Helpers sesión ─────
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
    #  ⇣⇣⇣  SOLO ASCII (sin tilde)  ⇣⇣⇣
    cal.add('prodid', '-//Saint Honore Pedidos//ES')
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

