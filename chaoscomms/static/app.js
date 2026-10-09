const setText = (id, value) => { document.getElementById(id).textContent = value ?? "—"; };

const selectRadio = async (radioId) => {
  try {
    const response = await fetch(`/api/v1/radios/${encodeURIComponent(radioId)}/select`, {
      method: "POST",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await Promise.all([refreshHealth(), refreshFleet()]);
  } catch (error) {
    setText("radio-error", "Unable to select radio");
  }
};

const renderFleet = (radios) => {
  const fleet = document.getElementById("radio-fleet");
  fleet.replaceChildren(...radios.map((radio) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "fleet-row";
    row.classList.toggle("fleet-row-active", radio.active === true);
    row.setAttribute("aria-pressed", radio.active === true ? "true" : "false");
    row.addEventListener("click", () => selectRadio(radio.id));
    const details = document.createElement("div");
    const name = document.createElement("div");
    name.className = "fleet-name";
    name.textContent = radio.model;
    const meta = document.createElement("div");
    meta.className = "fleet-meta";
    meta.textContent = `${radio.id} · ${radio.source}`;
    details.append(name, meta);
    const state = document.createElement("span");
    state.className = "fleet-state";
    state.textContent = radio.active ? "Active" : (radio.status.connected ? "Simulated" : "Offline");
    row.append(details, state);
    return row;
  }));
};

async function refreshFleet() {
  try {
    const response = await fetch("/api/v1/radios", { cache: "no-store" });
    if (response.ok) renderFleet((await response.json()).radios);
  } catch (error) {
    // The primary health status reports service availability.
  }
}

async function refreshHealth() {
  try {
    const response = await fetch("/api/v1/health", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const radio = payload.radio;
    setText("radio-model", radio.model);
    setText("frequency", radio.frequency_hz ? `${radio.frequency_hz.toLocaleString()} Hz` : "—");
    setText("mode", radio.mode || "—");
    setText("radio-error", radio.connected ? "Connected" : (radio.error || "Radio unavailable"));
    setText("updated", `Updated ${new Date().toLocaleTimeString()}`);
    const state = document.getElementById("service-state");
    state.textContent = payload.status === "ok" ? "Online" : "Standby";
    state.className = `pill ${payload.status === "ok" ? "pill-ok" : "pill-warn"}`;
  } catch (error) {
    setText("radio-error", "Service unavailable");
    const state = document.getElementById("service-state");
    state.textContent = "Offline";
    state.className = "pill pill-warn";
  }
}

refreshHealth();
refreshFleet();
setInterval(refreshHealth, 5000);
setInterval(refreshFleet, 5000);
