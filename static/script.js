document.addEventListener("DOMContentLoaded", async () => {
  const providerSel = document.getElementById("provider-select");
  const countrySel  = document.getElementById("country-select");
  const calendarEl  = document.getElementById("calendar");
  const API = "/api";

  /* =======================================================
     FullCalendar
  ======================================================= */
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto",
    buttonText: {
      today: "Hoy"
    }
  });
  calendar.render();

  /* =======================================================
     Helper: fetch JSON con manejo de expiración de sesión
  ======================================================= */
  async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) {
      alert("Tu sesión expiró. Inicia sesión de nuevo.");
      window.location.href = "/login";
      return [];
    }
    return res.json();
  }

  /* =======================================================
     1) Poblar proveedores
  ======================================================= */
  const providers = await fetchJson(`${API}/providers`);
  providers.forEach(p => providerSel.add(new Option(p, p)));

  /* =======================================================
     2) Cambio de Proveedor
  ======================================================= */
  providerSel.addEventListener("change", async e => {
    // Reseteo país + calendario
    calendar.removeAllEvents();
    countrySel.innerHTML = '<option value="">— Elegir —</option>';
    countrySel.disabled = true;

    const provider = e.target.value;
    if (!provider) return;

    // Cargo países
    const countries = await fetchJson(`${API}/countries?provider=${encodeURIComponent(provider)}`);
    countries.forEach(c => countrySel.add(new Option(c, c)));
    countrySel.disabled = false;
  });

  /* =======================================================
     3) Cambio de País => Eventos
  ======================================================= */
  countrySel.addEventListener("change", async e => {
    calendar.removeAllEvents();

    const provider = providerSel.value;
    const country  = e.target.value;
    if (!provider || !country) return;

    const evts = await fetchJson(`${API}/events?provider=${encodeURIComponent(provider)}&country=${encodeURIComponent(country)}`);
    calendar.addEventSource(evts);
  });
});

