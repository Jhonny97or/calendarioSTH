document.addEventListener("DOMContentLoaded", async () => {
  const providerSel = document.getElementById("provider-select");
  const countrySel  = document.getElementById("country-select");
  const calendarEl  = document.getElementById("calendar");
  const API = "/api";

  /* Calendar */
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto"
  });
  calendar.render();

  /* Util fetch JSON con manejo de error */
  async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
      alert("Tu sesión expiró: vuelve a iniciar sesión.");
      window.location.href = "/login";
      return [];
    }
    return res.json();
  }

  /* Cargar proveedores */
  for (const p of await fetchJson(`${API}/providers`))
    providerSel.add(new Option(p, p));

  /* Cambio de proveedor */
  providerSel.addEventListener("change", async e => {
    calendar.removeAllEvents();
    countrySel.innerHTML = '<option value="">— Elegir —</option>';
    countrySel.disabled = true;

    const provider = e.target.value;
    if (!provider) return;

    for (const c of await fetchJson(`${API}/countries?provider=${encodeURIComponent(provider)}`))
      countrySel.add(new Option(c, c));
    countrySel.disabled = false;
  });

  /* Cambio de país */
  countrySel.addEventListener("change", async e => {
    calendar.removeAllEvents();
    const provider = providerSel.value,
          country  = e.target.value;
    if (!provider || !country) return;
    const evts = await fetchJson(`${API}/events?provider=${encodeURIComponent(provider)}&country=${encodeURIComponent(country)}`);
    calendar.addEventSource(evts);
  });
});

