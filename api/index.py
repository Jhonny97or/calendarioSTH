from fastapi import FastAPI, Request, Form, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---- simple “database” -----
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}  # brand1…brand10
EVENTS = [
    # provider, brand, "YYYY-MM-DD"
    ("Proveedor A", "brand1", "2025-06-18"),
    ("Proveedor A", "brand2", "2025-07-22"),
    ("Proveedor B", "brand3", "2025-06-30"),
    ("Proveedor C", "brand1", "2025-08-05"),
    ("Proveedor C", "brand4", "2025-06-25"),
    # …añade más
]

# ---- cookie signer -----
signer = Signer("🔐-hard-replace-me-with-env-secret")

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

# ---- routes -----
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if get_user(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales incorrectas"})
    resp = RedirectResponse("/", 303)
    resp.set_cookie("session", signer.sign(username.encode()).decode(), httponly=True, max_age=86400*30)
    return resp

@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", 303)
    resp.delete_cookie("session")
    return resp

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: str = Depends(require_user)):
    return templates.TemplateResponse("calendar.html", {"request": request, "user": user})

@app.get("/events")
async def events(provider: str, user: str = Depends(require_user)):
    """Return JSON events for the selected provider *and* for the logged-in brand only."""
    provider_events = [
        {
            "title": f"Pedido • {p}",
            "start": d,
            "allDay": True
        }
        for p, brand, d in EVENTS
        if p == provider and brand == user
    ]
    return JSONResponse(provider_events)
