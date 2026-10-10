const setText = (id, value) => { document.getElementById(id).textContent = value ?? "—"; };

let audioSocket = null;
let audioContext = null;
let nextAudioTime = 0;

const stopAudio = () => {
  if (audioSocket) audioSocket.close();
  audioSocket = null;
  if (audioContext) audioContext.close();
  audioContext = null;
  nextAudioTime = 0;
  setText("audio-state", "Stopped");
  document.getElementById("audio-toggle").textContent = "Start audio";
};

const playPcmChunk = (buffer) => {
  if (!audioContext) return;
  const samples = new Int16Array(buffer);
  const frames = Math.floor(samples.length / 2);
  const audioBuffer = audioContext.createBuffer(2, frames, 48000);
  const left = audioBuffer.getChannelData(0);
  const right = audioBuffer.getChannelData(1);
  for (let i = 0; i < frames; i += 1) {
    left[i] = samples[i * 2] / 32768;
    right[i] = samples[i * 2 + 1] / 32768;
  }
  nextAudioTime = Math.max(nextAudioTime, audioContext.currentTime + 0.05);
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start(nextAudioTime);
  nextAudioTime += audioBuffer.duration;
};

const startAudio = async () => {
  audioContext = new AudioContext();
  await audioContext.resume();
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  audioSocket = new WebSocket(`${protocol}://${location.host}/api/v1/audio/stream`);
  audioSocket.binaryType = "arraybuffer";
  audioSocket.onopen = () => {
    setText("audio-state", "Playing");
    document.getElementById("audio-toggle").textContent = "Stop audio";
  };
  audioSocket.onmessage = (event) => playPcmChunk(event.data);
  audioSocket.onerror = () => {
    setText("audio-state", "Error");
    stopAudio();
  };
  audioSocket.onclose = () => {
    if (audioSocket) stopAudio();
  };
};

const toggleAudio = async () => {
  if (audioSocket) stopAudio();
  else await startAudio();
};

document.getElementById("audio-toggle").addEventListener("click", toggleAudio);

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
