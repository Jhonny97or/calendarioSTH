import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

import pandas as pd
from datetime import date
from functools import lru_cache

# ── Rutas base ─────────────────────────────────────────────────────────────
# __file__ apunta a .../app/api/index.py
BASE_DIR      = Path(__file__).resolve().parent.parent   # .../app
STATIC_DIR    = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# ── Busca el Excel en /app o en /app/static ────────────────────────────────
def find_excel_path() -> Path:
    candidates = [
        BASE_DIR / "deadlines.xlsx",
        STATIC_DIR / "deadlines.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "deadlines.xlsx no encontrado en:\n  " +
        "\n  ".join(str(p) for p in candidates)
    )
EXCEL_PATH = find_excel_path()

# ── App y mounts ─────────────────────────────────────────────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ── Credenciales demo ────────────────────────────────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

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

# ── Leer deadlines.xlsx ───────────────────────────────────────────────────
SPANISH_MONTHS = {
    'ene':1,'feb':2,'mar':3,'abr':4,
    'may':5,'jun':6,'jul':7,'ago':8,
    'sep':9,'oct':10,'nov':11,'dic':12
}

def parse_spanish_date(s: str) -> str:
    """
    Convierte '30-ene-25' en '2025-01-30'.
    """
    try:
        day, mon_abbr, yy = s.split('-')
        year  = 2000 + int(yy)
        month = SPANISH_MONTHS[mon_abbr.lower()]
        return date(year, month, int(day)).isoformat()
    except Exception as e:
        raise ValueError(f"Formato inválido en fecha '{s}': {e}")

@lru_cache(maxsize=1)
def load_events_from_excel():
    # Si algo falla aquí, devolvemos un HTTPException para verlo en el navegador
    try:
        df = pd.read_excel(str(EXCEL_PATH), engine="openpyxl")
    except FileNotFoundError as fnf:
        raise HTTPException(500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(500, detail=f"Error leyendo Excel: {e}")

    events = []
    for idx, row in df.iterrows():
        try:
            events.append({
                "proveedor": row.get("PROVEEDOR", "Proveedor1"),
                "pais":      row["PAIS"],
                "marca":     row["MARCA"],
                "user":      row.get("USER", "brand1"),
                "fecha_iso": parse_spanish_date(row["DEADLINE PROVEEDOR"])
            })
        except Exception as e:
            raise HTTPException(
                500,
                detail=f"Error en fila {idx} del Excel: {e}"
            )
    return events

# ── Rutas de autenticación ────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if _get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request,
               username: str = Form(...),
               password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales incorrectas"}
        )
    resp = RedirectResponse("/", 303)
    resp.set_cookie(
        "session",
        signer.sign(username.encode()).decode(),
        httponly=True,
        max_age=60*60*24*30,
        path="/",
        samesite="lax"
    )
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", 303)
    resp.delete_cookie("session", path="/")
    return resp

# ── Página principal ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse(
        "calendar.html",
        {"request": request, "user": user}
    )

# ── API JSON ──────────────────────────────────────────────────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(_require_user)):
    provs = {
        ev["proveedor"]
        for ev in load_events_from_excel()
        if ev["user"] == user
    }
    return JSONResponse(sorted(provs))

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(_require_user)):
    ctries = {
        ev["pais"]
        for ev in load_events_from_excel()
        if ev["proveedor"] == provider and ev["user"] == user
    }
    return JSONResponse(sorted(ctries))

@app.get("/api/events")
def api_events(provider: str,
               country: str,
               user: str = Depends(_require_user)):
    datos = []
    for ev in load_events_from_excel():
        if (ev["proveedor"], ev["pais"], ev["user"]) == (provider, country, user):
            datos.append({
                "title":           f"{ev['marca']} – PEDIDO",
                "start":           ev["fecha_iso"],
                "allDay":          True,
                "backgroundColor": "#f58220",
                "borderColor":     "#f58220"
            })
    return JSONResponse(datos)

