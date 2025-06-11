"""
Saint Honoré · Demand Planning (API / FastAPI)

Coloca este archivo en  calendarioSTH/api/index.py
"""

import os
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

# ────────────────────────────────────────────────────────────────────────
# Configuración básica
# ────────────────────────────────────────────────────────────────────────
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Si la variable no existe en Vercel durante el primer deploy,
# evitamos un crash (reemplázala en Prod por variable secreta real)
SESSION_SECRET = os.getenv("SESSION_SECRET", "DEMO_SESSION_SECRET")
signer = Signer(SESSION_SECRET)

# ────────────────────────────────────────────────────────────────────────
# Datos DEMO (reemplaza por conexión a DB o lectura de Excel)
# ────────────────────────────────────────────────────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}
#  (Proveedor,   Brand,    País,       Fecha ISO)
EVENTS = [
    ("Proveedor A", "brand1", "Colombia", "2025-07-04"),
    ("Proveedor A", "brand1", "Panamá",   "2025-07-18"),
    ("Proveedor A", "brand2", "Colombia", "2025-07-22"),
    ("Proveedor B", "brand3", "Chile",    "2025-06-30"),
    ("Proveedor C", "brand1", "México",   "2025-08-05"),
    ("Proveedor C", "brand4", "Colombia", "2025-06-25"),
]

# ────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────
def _eq(a: str, b: str) -> bool:
    """Compara dos strings ignorando mayúsculas y espacios laterales."""
    return a.strip().lower() == b.strip().lower()

def get_user(request: Request):
    cookie = request.cookies.get("session")
    if not cookie:
        return None
    try:
        return signer.unsign(cookie).decode()
    except BadSignature:
        return None

def require_user(request: Request):
    user = get_user(request)
    if not user:
        # 303 → redirección "See Other"
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

# ────────────────────────────────────────────────────────────────────────
# Autenticación
# ────────────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    # Si ya hay sesión, redirigir al home
    if get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
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
        max_age=60 * 60 * 24 * 30,  # 30 días
        path="/",
        samesite="lax"
    )
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", 303)
    resp.delete_cookie("session", path="/")
    return resp

# ────────────────────────────────────────────────────────────────────────
# Páginas HTML
# ────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(require_user)):
    return templates.TemplateResponse("calendar.html", {"request": request, "user": user})

# ────────────────────────────────────────────────────────────────────────
# Endpoints JSON (prefijo /api)
# ────────────────────────────────────────────────────────────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(require_user)):
    """
    Devuelve lista de proveedores visibles para la marca del usuario.
    """
    providers = sorted({p for p, brand, *_ in EVENTS if _eq(brand, user)})
    return JSONResponse(providers)

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(require_user)):
    countries = sorted({
        country for p, brand, country, *_ in EVENTS
        if _eq(p, provider) and _eq(brand, user)
    })
    return JSONResponse(countries)

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(require_user)):
    data = [
        {
            "title": f"Pedido · {provider}",
            "start": date_iso,
            "allDay": True
        }
        for p, brand, ctry, date_iso in EVENTS
        if _eq(p, provider) and _eq(ctry, country) and _eq(brand, user)
    ]
    return JSONResponse(data)


