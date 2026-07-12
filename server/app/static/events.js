function applyPower(data) {
  if (data.address && !ui.powerAddress.value.trim()) {
    ui.powerAddress.value = data.address;
    savePowerAddress();
  }
  ui.powerStatus.textContent = data.error || (data.enabled ? "Light pulse sent" : "Ready");
  ui.powerStatus.title = ui.powerStatus.textContent;
}

function loadPowerAddress() {
  ui.powerAddress.value = localStorage.getItem(powerAddressStorageKey) || "";
}

function savePowerAddress() {
  localStorage.setItem(powerAddressStorageKey, ui.powerAddress.value.trim());
}

function applyLatency(data) {
  if (!data || data.status === "waiting") {
    ui.latencyValue.value = "Latency: unknown";
    ui.latencyValue.title = "Click Calibrate to measure camera latency";
    ui.latencyStart.disabled = false;
    return;
  }
  if (data.status === "calculating") {
    ui.latencyValue.value = "Latency: calculating";
    ui.latencyValue.title = "3-second camera-move latency probe is running";
    ui.latencyStart.disabled = true;
    return;
  }
  ui.latencyStart.disabled = false;
  if (data.status === "done") {
    const seconds = Math.max(0.1, Number(data.seconds) || 0);
    ui.latencyValue.value = `Latency: ${seconds.toFixed(1)}s`;
    ui.latencyValue.title = "Measured from ONVIF move to visible RTSP frame change";
    return;
  }
  ui.latencyValue.value = "Latency: unavailable";
  ui.latencyValue.title = data.error || "3-second latency probe failed";
}

function startLatency() {
  ui.latencyValue.value = "Latency: calculating";
  ui.latencyValue.title = "3-second camera-move latency probe is running";
  ui.latencyStart.disabled = true;
  fetch("/api/latency/start", { method: "POST", cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(applyLatency)
    .catch(() => {
      ui.latencyValue.value = "Latency: offline";
      ui.latencyValue.title = "Latency probe start request failed";
      ui.latencyStart.disabled = false;
    });
}

function flashPower() {
  const address = ui.powerAddress.value.trim();
  savePowerAddress();
  if (!address) {
    ui.powerStatus.textContent = "LED controller UDP address is required";
    ui.powerStatus.title = ui.powerStatus.textContent;
    return;
  }
  ui.powerOn.disabled = true;
  ui.powerAddress.disabled = true;
  postJson("/api/light", { enabled: true, address })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(applyPower)
    .catch((error) => {
      ui.powerStatus.textContent = `Light pulse request failed: ${error.message}`;
      ui.powerStatus.title = ui.powerStatus.textContent;
    })
    .finally(() => {
      ui.powerOn.disabled = false;
      ui.powerAddress.disabled = false;
    });
}

function bindEvents() {
  [ui.horizontal, ui.vertical].forEach((slider) => {
    slider.addEventListener("input", () => {
      applyLimits();
      renderValues();
      sendDirection();
    });
    slider.addEventListener("click", handleSliderClick);
  });
  ui.vertical.addEventListener("keydown", handleVerticalSliderKeydown);
  limitInputs.forEach((input) => bindLimitInput(input));
  ui.motionSize.addEventListener("input", () => {
    renderValues();
    sendMotionSize();
  });
  ui.motionSizeDown.addEventListener("click", () => adjustMotionSize(-1));
  ui.motionSizeUp.addEventListener("click", () => adjustMotionSize(1));
  ui.record.addEventListener("click", toggleRecording);
  ui.latencyStart.addEventListener("click", startLatency);
  ui.motionOn.addEventListener("change", toggleMotion);
  ui.motionSound.addEventListener("change", toggleMotionSound);
  ui.powerAddress.addEventListener("change", savePowerAddress);
  ui.powerOn.addEventListener("click", flashPower);
  document.addEventListener("keydown", handleKeydown);
}

function adjustMotionSize(delta) {
  const min = Number(ui.motionSize.min) || 1;
  const max = Number(ui.motionSize.max) || 50;
  ui.motionSize.value = Math.max(min, Math.min(max, Number(ui.motionSize.value) + delta));
  renderValues();
  sendMotionSize();
}

function bindLimitInput(input) {
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    input.value = input.id.endsWith("H") ? ui.horizontal.value : ui.vertical.value;
    applyLimits(true, input.id);
    input.select();
  });
  input.addEventListener("change", () => applyLimits(true, input.id));
}

function handleSliderClick(event) {
  if (!event.metaKey) return;
  event.preventDefault();
  const isHorizontal = event.currentTarget === ui.horizontal;
  setDirection(isHorizontal ? 0 : Number(ui.horizontal.value), isHorizontal ? Number(ui.vertical.value) : 0);
}

function handleVerticalSliderKeydown(event) {
  const moves = {
    ArrowUp: 1,
    ArrowDown: -1,
  };
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    event.preventDefault();
    return;
  }
  const delta = moves[event.key];
  if (!delta) return;
  event.preventDefault();
  setDirection(Number(ui.horizontal.value), Number(ui.vertical.value) + delta);
}

function handleKeydown(event) {
  if (event.target instanceof HTMLInputElement) return;
  if (event.key.toLowerCase() === "m") {
    event.preventDefault();
    toggleMotionFromKey();
    return;
  }
  const moves = {
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
    ArrowUp: [0, 1],
    ArrowDown: [0, -1],
  };
  const move = moves[event.key];
  if (!move) return;
  event.preventDefault();
  moveBy(move[0], move[1]);
}
