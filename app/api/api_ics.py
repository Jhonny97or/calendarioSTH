# api_ics.py  (mismo nivel que tu index.py)
from fastapi import APIRouter, Depends, Response
from icalendar import Calendar, Event
from datetime import date, datetime
import pytz

router = APIRouter()

@router.get("/ics")
def export_ics(provider: str, country: str, user: str = Depends(_require_user)):
    # 1) filtra tus eventos existentes
    eventos = [
        ev for ev in load_events_manual()
        if (ev["proveedor"], ev["pais"], ev["user"]) == (provider, country, user)
    ]

    # 2) construye el iCalendar
    cal = Calendar()
    cal.add("prodid", "-//STH//Pedidos//")
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")

    for ev in eventos:
        e = Event()
        e.add("uid", f"{ev['marca']}-{ev['fecha_iso']}@sth")
        e.add("summary", f"{ev['marca']} – PEDIDO")
        d = date.fromisoformat(ev["fecha_iso"])
        e.add("dtstart", d)
        e.add("dtend",   d)               # evento de día completo
        e.add("dtstamp", datetime.utcnow().replace(tzinfo=pytz.UTC))
        cal.add_component(e)

    return Response(
        cal.to_ical(),
        media_type="text/calendar; charset=utf-8; method=PUBLISH",
        headers={"Content-Disposition": 'attachment; filename="pedidos.ics"'}
    )
