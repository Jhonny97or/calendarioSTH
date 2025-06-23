import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
signer = Signer(os.environ["SESSION_SECRET"])

# ── Credenciales demo ────────────────────────────────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

# ── Datos demo (proveedor, país, marca, usuario, fecha ISO) ──────────────
EVENTS = [
    ("Proveedor1", "Panamá",  "CHANEL",   "brand1", "2025-07-20"),
    ("Proveedor1", "Colombia","CHANEL",   "brand1", "2025-07-04"),
    ("Proveedor1", "Panamá",  "DIOR",     "brand1", "2025-08-18"),
    ("Proveedor2", "Chile",   "GUCCI",    "brand3", "2025-06-30"),
    ("Proveedor2", "Panamá",  "LACOSTE",  "brand3", "2025-09-10"),
]

# ── Helpers de sesión ───────────────────────────────────────────────────
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

# ── Auth ────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if _get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
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
    r = RedirectResponse("/login", 303)
    r.delete_cookie("session", path="/")
    return r

# ── Página principal ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse("calendar.html", {"request": request, "user": user})

# ── API JSON ────────────────────────────────────────────────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(_require_user)):
    provs = {p for p, _, _, u, _ in EVENTS if u == user}
    return JSONResponse(sorted(provs))

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(_require_user)):
    ctries = {c for p, c, _, u, _ in EVENTS if p == provider and u == user}
    return JSONResponse(sorted(ctries))

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(_require_user)):
    datos = [
        {
            "title": f"{brand} – PEDIDO",
            "start": fecha_iso,
            "allDay": True,
            "backgroundColor": "#f58220",
            "borderColor": "#f58220"
        }
        for p, c, brand, u, fecha_iso in EVENTS
        if (p, c, u) == (provider, country, user)
    ]
    return JSONResponse(datos)
