### main.py

```python
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
REPO_ROOT     = Path(__file__).resolve().parent.parent.parent
STATIC_DIR    = REPO_ROOT / "static"
TEMPLATES_DIR = REPO_ROOT / "templates"

# ────────────  App  ────────────────
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
signer = Signer(os.environ.get("SESSION_SECRET", "dev-secret"))

# ─────────────────── Datos de ejemplo ──────────────────────────────────────
#  (Proveedor, Marca, País, Fecha)
RAW_EVENTS = [
    # ... (todos tus eventos) ...
    # ——— Eventos nuevos para PANAMÁ ———
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
    d, m, yy = s.split("-")
    return date(2000 + int(yy), SPANISH_MONTHS[m.lower()], int(d)).isoformat()

@lru_cache(maxsize=1)
def load_events_manual():
    events = []
    for prov, marca, pais, fecha in RAW_EVENTS:
        if not fecha:
            continue
        events.append({
            "proveedor": prov,
            "marca": marca,
            "pais": pais,
            "fecha_iso": parse_spanish_date(fecha),
        })
    return events

# ───────────  Auth ───────────
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

# ───────  Login / Logout ───────
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if _get_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    CREDENTIALS = {f"brand{i}": f"brand{i}" for i in range(1, 11)}
    if CREDENTIALS.get(username) != password:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Credenciales incorrectas"}
        )
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(
        key="session",
        value=signer.sign(username.encode()).decode(),
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        path="/",
        samesite="lax"
    )
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session", path="/")
    return resp

# ───────────  Home ───────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(_require_user)):
    return templates.TemplateResponse(
        "calendar.html", {"request": request, "user": user}
    )

# ───────────  API JSON ───────────
@app.get("/api/countries")
def api_countries(user: str = Depends(_require_user)):
    # Devuelve todos los países
    countries = {ev["pais"] for ev in load_events_manual()}
    return JSONResponse(sorted(countries))

@app.get("/api/events")
def api_events(country: str, user: str = Depends(_require_user)):
    items = []
    for ev in load_events_manual():
        if ev["pais"] == country:
            items.append({
                "title": f"{ev['marca']} – PEDIDO",
                "start": ev["fecha_iso"],
                "allDay": True,
                "backgroundColor": "#f58220",
                "borderColor": "#f58220",
            })
    return JSONResponse(items)
```

### templates/calendar.html

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Saint Honoré · Calendario</title>
  <link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">
  <link href="/static/style.css" rel="stylesheet">
</head>
<body>
  <header>
    <div class="logo-wrap">
      <img src="/static/logo.png" alt="Saint Honoré">
      <span>Demand Planning</span>
    </div>
    <div>
      <strong>{{ user }}</strong> · <a href="/logout">Salir</a>
    </div>
  </header>

  <section class="filters">
    <label>Proveedor:
      <select id="provider-select">
        <option value="">— Elegir —</option>
      </select>
    </label>

    <label>País:
      <select id="country-select" disabled>
        <option value="">— Elegir —</option>
      </select>
    </label>

    <a id="btn-ics" class="btn" href="#" download style="display:none">
      Descargar ICS
    </a>
  </section>

  <div id="calendar"></div>

  <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      const calendarEl = document.getElementById('calendar');
      const calendar = new FullCalendar.Calendar(calendarEl, { initialView: 'dayGridMonth' });
      calendar.render();

      const provSel = document.getElementById('provider-select');
      const countrySel = document.getElementById('country-select');
      const icsBtn    = document.getElementById('btn-ics');

      // 1) Cargar proveedores
      fetch('/api/providers')
        .then(res => res.json())
        .then(list => {
          list.forEach(p => provSel.add(new Option(p, p)));
        });

      // 2) Al cambiar proveedor, habilitar país y cargar países
      provSel.addEventListener('change', function() {
        countrySel.innerHTML = '<option value="">— Elegir —</option>';
        const prov = this.value;
        if (!prov) {
          countrySel.disabled = true;
          calendar.removeAllEvents();
          icsBtn.style.display = 'none';
          return;
        }
        countrySel.disabled = false;
        fetch(`/api/countries?provider=${encodeURIComponent(prov)}`)
          .then(res => res.json())
          .then(list => list.forEach(c => countrySel.add(new Option(c, c))));
      });

      // 3) Al cambiar país, cargar eventos y mostrar ICS
      countrySel.addEventListener('change', function() {
        const prov = provSel.value;
        const country = this.value;
        calendar.removeAllEvents();
        icsBtn.style.display = 'none';
        if (!prov || !country) return;

        // JSON events
        fetch(`/api/events?provider=${encodeURIComponent(prov)}&country=${encodeURIComponent(country)}`)
          .then(res => res.json())
          .then(events => {
            calendar.addEventSource(events);
          });

        // Link a ICS (implementar ruta /api/ics si la tienes)
        icsBtn.href = `/api/ics?provider=${encodeURIComponent(prov)}&country=${encodeURIComponent(country)}`;
        icsBtn.style.display = 'inline-block';
      });
    });
  </script>
</body>
</html>
```


