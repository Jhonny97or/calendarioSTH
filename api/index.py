"""
Saint Honoré · Demand Planning  ·  FastAPI
Ruta: calendarioSTH/api/index.py
"""

import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

# ───────────────────────────────────────────
# Config básica
# ───────────────────────────────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

signer = Signer(os.getenv("SESSION_SECRET", "DEMO_SECRET"))

# ───────────────────────────────────────────
# Datos DEMO
#  (Proveedor, Brand,  País,       Fecha ISO)
# ───────────────────────────────────────────
EVENTS = [
    ("Proveedor1", "brand1", "Colombia", "2025-08-06"),
    ("Proveedor1", "brand1", "Panamá",   "2025-08-20"),
    ("Proveedor2", "brand1", "Chile",    "2025-09-01"),
    ("Proveedor2", "brand2", "Colombia", "2025-09-10"),
]

CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

# ───────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────
def _eq(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()

def get_user(req: Request):
    cookie = req.cookies.get("session")
    if not cookie:
        return None
    try:
        return signer.unsign(cookie).decode()
    except BadSignature:
        return None

def require_user(req: Request):
    user = get_user(req)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

def no_cache(payload):
    """Devuelve JSONResponse sin caché."""
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})

# ───────────────────────────────────────────
# Auth
# ───────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(req: Request):
    if get_user(req):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": req, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(req: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {"request": req, "error": "Credenciales incorrectas"})
    resp = RedirectResponse("/", 303)
    resp.set_cookie(
        "session",
        signer.sign(username.encode()).decode(),
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        path="/",
        samesite="lax"
    )
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", 303)
    resp.delete_cookie("session", path="/")
    return resp

# ───────────────────────────────────────────
# Páginas
# ───────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(req: Request, user: str = Depends(require_user)):
    return templates.TemplateResponse("calendar.html", {"request": req, "user": user})

# ───────────────────────────────────────────
# API JSON
# ───────────────────────────────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(require_user)):
    provs = sorted({p for p, brand, *_ in EVENTS if _eq(brand, user)})
    # Log rápido en Vercel para depurar
    print(f"[providers] user={user} → {provs}")
    return no_cache(provs)

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(require_user)):
    ctries = sorted({
        country for p, brand, country, _ in EVENTS
        if _eq(p, provider) and _eq(brand, user)
    })
    return no_cache(ctries)

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(require_user)):
    evts = [
        {"title": f"Pedido · {provider}", "start": date_iso, "allDay": True}
        for p, brand, country_evt, date_iso in EVENTS
        if _eq(p, provider) and _eq(country_evt, country) and _eq(brand, user)
    ]
    return no_cache(evts)


