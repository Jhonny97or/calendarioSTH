document.addEventListener("DOMContentLoaded", () => {
  const providerSelect = document.getElementById("provider-select");
  const calendarEl    = document.getElementById("calendar");

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    height: "auto",
    selectable: false,
    events: []   // empty until provider chosen
  });
  calendar.render();

  providerSelect.addEventListener("change", async e => {
    calendar.removeAllEvents();
    const provider = e.target.value;
    if (!provider) return;
    const res = await fetch(`/events?provider=${encodeURIComponent(provider)}`);
    if (res.ok) {
      const evts = await res.json();
      calendar.addEventSource(evts);
    }
  });
});
