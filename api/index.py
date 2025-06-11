# ─── API JSON (prefijo /api) ─────────────────────────────────────────────
def _eq(a: str, b: str) -> bool:
    """Comparación robusta (ignora mayúsculas y espacios)."""
    return a.strip().lower() == b.strip().lower()

@app.get("/api/providers")
def api_providers(user: str = Depends(require_user)):
    provs = sorted({p for p, b, *_ in EVENTS if _eq(b, user)})
    return JSONResponse(provs)

@app.get("/api/countries")
def api_countries(provider: str, user: str = Depends(require_user)):
    ctries = sorted(
        {c for p, b, c, _ in EVENTS if _eq(p, provider) and _eq(b, user)}
    )
    return JSONResponse(ctries)

@app.get("/api/events")
def api_events(provider: str, country: str, user: str = Depends(require_user)):
    evts = [
        {
            "title": f"Pedido · {provider}",
            "start": date,
            "allDay": True
        }
        for p, b, c, date in EVENTS
        if _eq(p, provider) and _eq(c, country) and _eq(b, user)
    ]
    return JSONResponse(evts)


