document.addEventListener("DOMContentLoaded", () => {
  const provSel = document.getElementById("provider-select");
  const ctrSel  = document.getElementById("country-select");

  // 1) Cargar proveedores
  fetch("/api/providers")
    .then(res => res.json())
    .then(providers => {
      providers.forEach(p => {
        const o = document.createElement("option");
        o.value = p;
        o.textContent = p;
        provSel.appendChild(o);
      });

      // Si solo hay uno, auto-selecciónalo y dispara el cambio
      if (providers.length === 1) {
        provSel.value = providers[0];
        provSel.dispatchEvent(new Event("change"));
      }
    });

  // 2) Al cambiar proveedor, recargar países y refrescar calendario
  provSel.addEventListener("change", () => {
    // limpiar país
    ctrSel.innerHTML = `<option value="">— Elegir —</option>`;
    // avisar al calendario para que no muestre eventos
    calendar.refetchEvents();

    const prov = provSel.value;
    if (!prov) return;

    fetch(`/api/countries?provider=${encodeURIComponent(prov)}`)
      .then(res => res.json())
      .then(countries => {
        countries.forEach(c => {
          const o = document.createElement("option");
          o.value = c;
          o.textContent = c;
          ctrSel.appendChild(o);
        });

        // auto-seleccionar si sólo hay uno
        if (countries.length === 1) {
          ctrSel.value = countries[0];
          calendar.refetchEvents();
        }
      });
  });

  // 3) Al cambiar país, refrescar calendario
  ctrSel.addEventListener("change", () => {
    calendar.refetchEvents();
  });

  // 4) Inicializar FullCalendar
  const calendarEl = document.getElementById("calendar");
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    locale: "es",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: ""
    },
    events: (fetchInfo, successCallback, failureCallback) => {
      const prov    = provSel.value;
      const country = ctrSel.value;

      if (!prov || !country) {
        // no hay suficientes filtros, devolvemos vacío
        successCallback([]);
        return;
      }

      fetch(
        `/api/events?provider=${encodeURIComponent(prov)}&country=${encodeURIComponent(country)}`
      )
        .then(res => {
          if (!res.ok) throw new Error("Error en la respuesta de eventos");
          return res.json();
        })
        .then(data => successCallback(data))
        .catch(err => failureCallback(err));
    }
  });

  calendar.render();
});
