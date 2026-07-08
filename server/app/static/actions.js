function applyMotion(data) {
  ui.motionOn.checked = Boolean(data.enabled);
}

function toggleMotion() {
  const enabled = ui.motionOn.checked;
  ui.motionOn.disabled = true;
  postJson("/api/motion", { enabled })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(applyMotion)
    .catch(() => { ui.motionOn.checked = !enabled; })
    .finally(() => { ui.motionOn.disabled = false; });
}

function toggleMotionFromKey() {
  ui.motionOn.checked = !ui.motionOn.checked;
  toggleMotion();
}

function setDirection(nextHorizontal, nextVertical) {
  normalizeLimits();
  ui.horizontal.value = clampHorizontal(nextHorizontal);
  ui.vertical.value = clampVertical(nextVertical);
  renderValues();
  sendDirection();
}

function moveBy(deltaHorizontal, deltaVertical) {
  setDirection(Number(ui.horizontal.value) + deltaHorizontal, Number(ui.vertical.value) + deltaVertical);
}

function centerDirection() {
  normalizeLimits();
  ui.horizontal.value = Math.round((limitValue(ui.minH, -100) + limitValue(ui.maxH, 100)) / 2);
  ui.vertical.value = Math.round((limitValue(ui.minV, -100) + limitValue(ui.maxV, 100)) / 2);
  renderValues();
  postDirection();
}

function renderFollow(data) {
  const steps = data.adjustments ? data.adjustments.length : 0;
  const maxSteps = clampSteps(ui.followSteps.value);
  ui.followStatus.textContent = `${data.status || "done"} · ${steps}/${maxSteps} · ${Math.round((data.lag_seconds || 1) * 1000)}ms`;
  ui.followStatus.title = ui.followStatus.textContent;
  if (data.direction) {
    ui.horizontal.value = clampHorizontal(data.direction.horizontal);
    ui.vertical.value = clampVertical(data.direction.vertical);
    renderValues();
  }
}

function runFollow() {
  ui.followSteps.value = clampSteps(ui.followSteps.value);
  ui.follow.disabled = true;
  ui.followSteps.disabled = true;
  ui.followStatus.textContent = "Following...";
  postJson("/api/follow", followPayload())
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(renderFollow)
    .catch((error) => {
      ui.followStatus.textContent = `Follow failed: ${error.message}`;
      ui.followStatus.title = ui.followStatus.textContent;
    })
    .finally(() => {
      ui.follow.disabled = false;
      ui.followSteps.disabled = false;
    });
}

function renderRecording(file, error) {
  ui.record.textContent = state.isRecording ? "Stop" : "Record";
  ui.record.classList.toggle("recording", state.isRecording);
  ui.recordStatus.textContent = error || (state.isRecording ? file || "Recording" : "Not recording");
  ui.recordStatus.title = ui.recordStatus.textContent;
}

function applyRecording(data) {
  state.isRecording = Boolean(data.recording);
  renderRecording(data.file, data.error || "");
}

function toggleRecording() {
  const path = state.isRecording ? "/api/recording/stop" : "/api/recording/start";
  ui.record.disabled = true;
  fetch(path, { method: "POST" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(applyRecording)
    .catch((error) => renderRecording("", `Recording request failed: ${error.message}`))
    .finally(() => { ui.record.disabled = false; });
}
