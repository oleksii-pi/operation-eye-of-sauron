function postJson(path, payload) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function postDirection() {
  return postJson("/api/direction", {
    horizontal: Number(ui.horizontal.value),
    vertical: Number(ui.vertical.value),
  }).catch(() => {});
}

function sendDirection() {
  clearTimeout(state.sendTimer);
  state.sendTimer = setTimeout(postDirection, 80);
}

function postMotionSize() {
  return postJson("/api/motion-size", {
    min_size_cm: Number(ui.motionSize.value),
  }).catch(() => {});
}

function sendMotionSize() {
  clearTimeout(state.motionTimer);
  state.motionTimer = setTimeout(postMotionSize, 120);
}

function updateLatency() {
  fetch("/api/status", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      applyLatency(data.latency);
      applyRecording(data.recording || {});
      applyMotor(data.motor || {});
    })
    .catch(() => {
      ui.latencyValue.value = "Latency: offline";
      ui.latencyValue.title = "Status request failed";
      ui.latencyStart.disabled = false;
    });
}

function loadStatus() {
  fetch("/api/status")
    .then((response) => response.json())
    .then((data) => {
      const detection = data.settings && data.settings.detection;
      if (detection && detection.min_size_cm) {
        ui.motionSize.value = detection.min_size_cm;
        applyMotion(detection);
        renderValues();
      }
      applyRecording(data.recording || {});
      applyLatency(data.latency);
      applyMotor(data.motor || {});
    })
    .catch(() => {});
}
