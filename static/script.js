document.addEventListener("DOMContentLoaded", async () => {
  const API   = "/api";
  const $prov = document.getElementById("provider-select");
  const $pais = document.getElementById("country-select");
  const calEl = document.getElementById("calendar");

  /* Calendar init */
  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto"
  });
  calendar.render();

  /* Helper fetch */
  async function j(url){
    const r = await fetch(url);
    if(!r.ok){ window.location.href="/login"; return []; }
    return r.json();
  }

  /* Cargar proveedores */
  (await j(`${API}/providers`))
      .forEach(p => $prov.add(new Option(p,p)));

  /* Cambio de proveedor */
  $prov.addEventListener("change", async e=>{
    calendar.removeAllEvents();
    $pais.innerHTML = '<option value="">— Elegir —</option>';
    $pais.disabled  = true;

    const prov = e.target.value;
    if(!prov) return;

    (await j(`${API}/countries?provider=${encodeURIComponent(prov)}`))
        .forEach(c => $pais.add(new Option(c,c)));
    $pais.disabled=false;
  });

  /* Cambio de país → trae eventos */
  $pais.addEventListener("change", async e=>{
    calendar.removeAllEvents();
    const prov = $prov.value,
          pais = e.target.value;
    if(!prov || !pais) return;

    const evts = await j(
      `${API}/events?provider=${encodeURIComponent(prov)}&country=${encodeURIComponent(pais)}`
    );
    calendar.addEventSource(evts);
  });
});
