# api/index.py
import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import Signer, BadSignature
from datetime import date
from functools import lru_cache

# ───────────  Rutas base  ───────────
# __file__ = .../api/index.py, parents[0]=api/, [1]=project-root/, [2]=... (por seguridad)
REPO_ROOT     = Path(__file__).resolve().parents[1]
STATIC_DIR    = REPO_ROOT / "static"
TEMPLATES_DIR = REPO_ROOT / "templates"

# ────────────  App  ────────────────
app = FastAPI()
# Esto ya no fallará, STATIC_DIR siempre apuntará a tu carpeta /static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ───────  Credenciales demo  ───────
CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}

# ──── Datos de ejemplo ────
RAW_EVENTS = [
    # ——— Proveedor1 (CHANEL) ———
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

    # (… resto de Proveedor1 y Proveedor2 …)

    # ——— Proveedor3 (PANAMÁ) + pedidos nuevos ———
    ("Proveedor3","ACTIUM",        "PANAMA","06-jul-25"),
    ("Proveedor3","AGENCIAS FEDURO","PANAMA","10-jul-25"),
    ("Proveedor3","BEAUTE PRESTIGE INTERNATIONAL SAS","PANAMA","06-jul-25"),
    ("Proveedor3","BELUXE LATAM SA","PANAMA","06-jul-25"),
    ("Proveedor3","DOLCE & GABBANA BEAUTY USA INC.","PANAMA","06-jul-25"),
    ("Proveedor3","ESSENCE CORPORATION","PANAMA","06-jul-25"),
    ("Proveedor3","ESTEE LAUDER AG LACHEN","PANAMA","06-jul-25"),
    ("Proveedor3","MLL BRAND IMPORT LLC","PANAMA","06-jul-25"),
    ("Proveedor3","SHISEIDO TRAVEL RETAIL AMERICAS","PANAMA","06-jul-25"),
    # meses siguientes…
    ("Proveedor3","PUIG",   "PANAMA","05-jun-25"),
    ("Proveedor3","MAC",    "PANAMA","15-jul-25"),
    ("Proveedor3","REVLON", "PANAMA","15-jul-25"),
    ("Proveedor3","CHARO",  "PANAMA","20-jun-25"),
    ("Proveedor3","BOGART/LAPIDUS","PANAMA","10-sep-25"),
    ("Proveedor3","LVMH",   "PANAMA","10-ago-25"),
    ("Proveedor3","NAT CORP","PANAMA","20-jun-25"),
    ("Proveedor3","RISE",   "PANAMA","10-jul-25"),
    ("Proveedor3","PUIG",   "PANAMA","05-sep-25"),
    ("Proveedor3","MAC",    "PANAMA","15-ago-25"),
    ("Proveedor3","REVLON", "PANAMA","15-sep-25"),
    ("Proveedor3","CHARO",  "PANAMA","20-oct-25"),
    ("Proveedor3","RISE",   "PANAMA","10-oct-25"),
    ("Proveedor3","PUIG",   "PANAMA","05-nov-25"),
    ("Proveedor3","MAC",    "PANAMA","15-sep-25"),
    ("Proveedor3","MAC",    "PANAMA","15-oct-25"),
    ("Proveedor3","MAC",    "PANAMA","15-nov-25"),
    ("Proveedor3","MAC",    "PANAMA","15-dic-25"),
]

SPANISH_MONTHS = {
  "ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,
  "jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12,
}

def parse_spanish_date(s: str) -> str:
    d,m,yy = s.split("-")
    return date(2000+int(yy), SPANISH_MONTHS[m.lower()], int(d)).isoformat()

@lru_cache(maxsize=1)
def load_events():
    return [
      {"proveedor":p, "marca":m, "pais":c, "fecha_iso":parse_spanish_date(f)}
      for p,m,c,f in RAW_EVENTS if f
    ]

def _get_user(req: Request):
    tok = req.cookies.get("session")
    if not tok: return None
    try: return signer.unsign(tok).decode()
    except BadSignature: return None

def _require_user(req: Request):
    u = _get_user(req)
    if not u:
        raise HTTPException(303, headers={"Location":"/login"})
    return u

@app.get("/login", response_class=HTMLResponse)
def login_get(req: Request):
    if _get_user(req): return RedirectResponse("/",303)
    return templates.TemplateResponse("login.html",{"request":req,"error":None})

@app.post("/login", response_class=HTMLResponse)
def login_post(req: Request, username: str = Form(...), password: str = Form(...)):
    if CREDENTIALS.get(username)!=password:
        return templates.TemplateResponse("login.html",
               {"request":req,"error":"Credenciales incorrectas"})
    r = RedirectResponse("/",303)
    r.set_cookie("session", signer.sign(username.encode()).decode(),
                 httponly=True, max_age=60*60*24*30,
                 path="/", samesite="lax")
    return r

@app.get("/logout")
def logout():
    r=RedirectResponse("/login",303)
    r.delete_cookie("session",path="/")
    return r

@app.get("/", response_class=HTMLResponse)
def home(req: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse("calendar.html",
                                      {"request":req,"user":user})

@app.get("/api/providers")
def api_providers(user: str = Depends(_require_user)):
    return JSONResponse(sorted({e["proveedor"] for e in load_events()}))

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(_require_user)):
    return JSONResponse(sorted({e["pais"] for e in load_events() if e["proveedor"] == provider}))

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(_require_user)):
    return JSONResponse([
      {"title":f"{e['marca']} – PEDIDO","start":e["fecha_iso"],"allDay":True,
       "backgroundColor":"#f58220","borderColor":"#f58220"}
      for e in load_events()
      if e["proveedor"]==provider and e["pais"]==country
    ])


