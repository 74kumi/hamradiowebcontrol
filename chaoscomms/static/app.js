const setText = (id, value) => { document.getElementById(id).textContent = value ?? "—"; };

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
setInterval(refreshHealth, 5000);
