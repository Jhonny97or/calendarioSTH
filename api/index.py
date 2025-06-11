import os
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature

# ── App & FS ─────────────────────────────────────────────────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
signer = Signer(os.environ["SESSION_SECRET"])

# ── “BD” de demo ─────────────────────────────────────────────────────────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

EVENTS = [
    # proveedor, marca, país, fecha ISO
    ("Proveedor A", "brand1", "Colombia", "2025-07-04"),
    ("Proveedor A", "brand1", "Panamá",   "2025-07-18"),
    ("Proveedor A", "brand2", "Colombia", "2025-07-22"),
    ("Proveedor B", "brand3", "Chile",    "2025-06-30"),
    ("Proveedor C", "brand1", "México",   "2025-08-05"),
    ("Proveedor C", "brand4", "Colombia", "2025-06-25"),
]

# ── Helpers ──────────────────────────────────────────────────────────────
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
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

# ── Auth ─────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
    resp = RedirectResponse("/", 303)
    resp.set_cookie("session", signer.sign(username.encode()).decode(), httponly=True, max_age=60*60*24*30)
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", 303)
    resp.delete_cookie("session")
    return resp

# ── UI principal ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(require_user)):
    return templates.TemplateResponse("calendar.html", {"request": request, "user": user})

# ── APIs de datos ────────────────────────────────────────────────────────
@app.get("/providers")
def providers(user: str = Depends(require_user)):
    provs = sorted({p for p, brand, *_ in EVENTS if brand == user})
    return JSONResponse(provs)

@app.get("/countries")
def countries(provider: str, user: str = Depends(require_user)):
    ctries = sorted({ctry for p, brand, ctry, *_ in EVENTS if p == provider and brand == user})
    return JSONResponse(ctries)

@app.get("/events")
def events(provider: str, country: str, user: str = Depends(require_user)):
    evts = [
        {"title": f"Pedido – {provider}", "start": date, "allDay": True}
        for p, brand, ctry, date in EVENTS
        if p == provider and ctry == country and brand == user
    ]
    return JSONResponse(evts)
