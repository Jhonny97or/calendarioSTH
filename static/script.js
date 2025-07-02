document.addEventListener("DOMContentLoaded", () => {
  const provSel  = document.getElementById("provider-select");
  const ctrSel   = document.getElementById("country-select");
  const icsBtn   = document.getElementById("btn-ics");  // enlace nuevo
  const calendarEl = document.getElementById("calendar");

  let currentProv = "";
  let currentCountry = "";

  /* — 1) Cargar proveedores — */
  fetch("/api/providers")
    .then(r => r.json())
    .then(provs => {
      provs.forEach(p => {
        const o = document.createElement("option");
        o.value = p;
        o.textContent = p;
        provSel.appendChild(o);
      });
      if (provs.length === 1) {
        provSel.value = provs[0];
        provSel.dispatchEvent(new Event("change"));
      }
    });

  /* — 4) Inicializar FullCalendar — */
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: ""
    },
    events: (fetchInfo, success, failure) => {
      if (!currentProv || !currentCountry) return success([]);
      fetch(`/api/events?provider=${encodeURIComponent(currentProv)}&country=${encodeURIComponent(currentCountry)}`)
        .then(r => {
          if (!r.ok) throw new Error("Error en eventos");
          return r.json();
        })
        .then(data => success(data))
        .catch(e => failure(e));
    }
  });
  calendar.render();

  /* — helper para actualizar el enlace ICS — */
  function updateIcsLink() {
    if (currentProv && currentCountry) {
      icsBtn.href = `/api/ics?provider=${encodeURIComponent(currentProv)}&country=${encodeURIComponent(currentCountry)}`;
      icsBtn.style.display = "inline-block";
    } else {
      icsBtn.style.display = "none";
    }
  }

  /* — 2) Cambio de proveedor — */
  provSel.addEventListener("change", () => {
    ctrSel.innerHTML = `<option value="">— Elegir —</option>`;
    calendar.refetchEvents();

    currentProv = provSel.value;
    currentCountry = "";
    updateIcsLink();

    if (!currentProv) return;

    fetch(`/api/countries?provider=${encodeURIComponent(currentProv)}`)
      .then(r => r.json())
      .then(countries => {
        countries.forEach(c => {
          const o = document.createElement("option");
          o.value = c;
          o.textContent = c;
          ctrSel.appendChild(o);
        });
        if (countries.length === 1) {
          ctrSel.value = countries[0];
          currentCountry = countries[0];
          calendar.refetchEvents();
          updateIcsLink();
        }
      });
  });

  /* — 3) Cambio de país — */
  ctrSel.addEventListener("change", () => {
    currentCountry = ctrSel.value;
    calendar.refetchEvents();
    updateIcsLink();
  });
});
