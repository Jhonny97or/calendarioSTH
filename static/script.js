document.addEventListener("DOMContentLoaded", async () => {
  const providerSel = document.getElementById("provider-select");
  const countrySel  = document.getElementById("country-select");
  const calendarEl  = document.getElementById("calendar");

  /* ── Calendar init ───────────────────────────── */
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto",
    events: []
  });
  calendar.render();

  /* ── Load providers for this usuario ─────────── */
  const provs = await (await fetch("/providers")).json();
  provs.forEach(p => {
    const opt = new Option(p, p);
    providerSel.add(opt);
  });

  /* ── When provider changes ───────────────────── */
  providerSel.addEventListener("change", async e => {
    calendar.removeAllEvents();
    countrySel.innerHTML = '<option value="">— Elegir —</option>';
    countrySel.disabled  = true;
    const provider = e.target.value;
    if (!provider) return;

    /* fetch countries */
    const countries = await (await fetch(`/countries?provider=${encodeURIComponent(provider)}`)).json();
    countries.forEach(c => countrySel.add(new Option(c, c)));
    countrySel.disabled = false;
  });

  /* ── When country changes ─────────────────────── */
  countrySel.addEventListener("change", async e => {
    calendar.removeAllEvents();
    const country   = e.target.value;
    const provider  = providerSel.value;
    if (!provider || !country) return;
    const evts = await (await fetch(`/events?provider=${encodeURIComponent(provider)}&country=${encodeURIComponent(country)}`)).json();
    calendar.addEventSource(evts);
  });
});
