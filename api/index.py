import os, datetime as dt
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

# ────────────────────────────────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
signer = Signer(os.environ["SESSION_SECRET"])

# ─── Seguridad DEMO ─────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}  # user = pwd

# (Proveedor,  Brand,   País,      Fecha ISO)
EVENTS = [
    ("Proveedor A", "brand1", "Colombia", "2025-07-04"),
    ("Proveedor A", "brand1", "Panamá",   "2025-07-18"),
    ("Proveedor A", "brand2", "Colombia", "2025-07-22"),
    ("Proveedor B", "brand3", "Chile",    "2025-06-30"),
    ("Proveedor C", "brand1", "México",   "2025-08-05"),
    ("Proveedor C", "brand4", "Colombia", "2025-06-25"),
]

# ─── Helpers ────────────────────────────────
def get_user(req: Request):
    raw = req.cookies.get("session")
    if not raw:
        return None
    try:
        return signer.unsign(raw).decode()
    except BadSignature:
        return None

def require_user(req: Request):
    user = get_user(req)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

# ─── Auth ───────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(req: Request):
    if get_user(req):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": req, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(
    req: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {"request": req, "error": "Credenciales incorrectas"})
    resp = RedirectResponse("/", 303)
    resp.set_cookie(
        "session",
        signer.sign(username.encode()).decode(),
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax",
        path="/"
    )
    return resp

@app.get("/logout")
def logout():
    r = RedirectResponse("/login", 303)
    r.delete_cookie("session", path="/")
    return r

# ─── Páginas HTML ───────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(req: Request, user: str = Depends(require_user)):
    return templates.TemplateResponse("calendar.html", {"request": req, "user": user})

# ─── API JSON (prefijo /api) ────────────────
@app.get("/api/providers")
def api_providers(user: str = Depends(require_user)):
    provs = sorted({p for p, b, *_ in EVENTS if b == user})
    return JSONResponse(provs)

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(require_user)):
    ctries = sorted({c for p, b, c, _ in EVENTS if p == provider and b == user})
    return JSONResponse(ctries)

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(require_user)):
    evts = [
        {
            "title": f"Pedido · {provider}",
            "start": d,
            "allDay": True
        }
        for p, b, c, d in EVENTS
        if p == provider and c == country and b == user
    ]
    return JSONResponse(evts)

