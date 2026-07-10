function applyMotor(data) {
  ui.motorOn.checked = Boolean(data.enabled);
  if (data.address && !ui.motorAddress.value.trim()) {
    ui.motorAddress.value = data.address;
    saveMotorAddress();
  }
  ui.motorStatus.textContent = data.error || "";
  ui.motorStatus.title = ui.motorStatus.textContent;
}

function loadMotorAddress() {
  ui.motorAddress.value = localStorage.getItem(motorAddressStorageKey) || "";
}

function saveMotorAddress() {
  localStorage.setItem(motorAddressStorageKey, ui.motorAddress.value.trim());
}

function renderFollowIdle() {
  ui.followStatus.textContent = `Follow idle · ${(state.streamLagMs / 1000).toFixed(1)}s`;
  ui.followStatus.title = ui.followStatus.textContent;
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
    state.streamLagMs = Math.round(seconds * 1000);
    ui.latencyValue.value = `Latency: ${seconds.toFixed(1)}s`;
    ui.latencyValue.title = "Measured from ONVIF move to visible RTSP frame change";
    if (ui.followStatus.textContent.startsWith("Follow idle")) renderFollowIdle();
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

function toggleMotor() {
  const enabled = ui.motorOn.checked;
  const address = ui.motorAddress.value.trim();
  saveMotorAddress();
  if (enabled && !address) {
    ui.motorOn.checked = false;
    ui.motorStatus.textContent = "Motor UDP address is required";
    ui.motorStatus.title = ui.motorStatus.textContent;
    return;
  }
  ui.motorOn.disabled = true;
  ui.motorAddress.disabled = true;
  postJson("/api/motor", { enabled, address })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(applyMotor)
    .catch((error) => {
      ui.motorOn.checked = !enabled;
      ui.motorStatus.textContent = `Motor request failed: ${error.message}`;
      ui.motorStatus.title = ui.motorStatus.textContent;
    })
    .finally(() => {
      ui.motorOn.disabled = false;
      ui.motorAddress.disabled = false;
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
  ui.record.addEventListener("click", toggleRecording);
  ui.follow.addEventListener("click", runFollow);
  ui.latencyStart.addEventListener("click", startLatency);
  ui.followSteps.addEventListener("change", () => {
    ui.followSteps.value = clampSteps(ui.followSteps.value);
  });
  ui.motionOn.addEventListener("change", toggleMotion);
  ui.motorAddress.addEventListener("change", saveMotorAddress);
  ui.motorOn.addEventListener("change", toggleMotor);
  ui.streamImage.addEventListener("load", renderFollowIdle, { once: true });
  document.addEventListener("keydown", handleKeydown);
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
