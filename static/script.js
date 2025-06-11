document.addEventListener("DOMContentLoaded", async () => {
  const API   = "/api";
  const $pais = document.getElementById("country-select");
  const calEl = document.getElementById("calendar");

  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto"
  });
  calendar.render();

  async function j(url){
    const r = await fetch(url);
    if(!r.ok){ location.href="/login"; return []; }
    return r.json();
  }

  // 1) Poblar países
  (await j(`${API}/countries`))
      .forEach(c => $pais.add(new Option(c,c)));

  // 2) Al cambiar país → eventos
  $pais.addEventListener("change", async e=>{
    calendar.removeAllEvents();
    const c = e.target.value;
    if(!c) return;
    calendar.addEventSource(await j(`${API}/events?country=${encodeURIComponent(c)}`));
  });
});
