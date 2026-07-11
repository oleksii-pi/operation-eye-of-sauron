function applyMotion(data) {
  ui.motionOn.checked = Boolean(data.enabled);
  syncMotionSound();
}

function loadMotionSound() {
  state.motionSoundEnabled = localStorage.getItem(motionSoundStorageKey) === "true";
  state.motionSound.preload = "auto";
  syncMotionSound();
}

function syncMotionSound() {
  ui.motionSoundRow.hidden = !ui.motionOn.checked;
  ui.motionSound.disabled = !ui.motionOn.checked;
  ui.motionSound.checked = state.motionSoundEnabled;
  if (!ui.motionOn.checked) resetMotionSoundState();
  if (!state.motionSoundEnabled) stopMotionSounds();
}

function toggleMotionSound() {
  state.motionSoundEnabled = ui.motionSound.checked;
  localStorage.setItem(motionSoundStorageKey, state.motionSoundEnabled ? "true" : "false");
  syncMotionSound();
}

function handleMotionDetection(data) {
  if (!data) return;
  applyMotion(data);
  const motionBoxes = data.enabled ? Math.max(0, Number(data.boxes) || 0) : 0;
  if (motionBoxes <= 0) {
    state.motionBoxCount = 0;
    return;
  }
  playMotionSounds(Math.max(0, motionBoxes - state.motionBoxCount));
  state.motionBoxCount = motionBoxes;
}

function playMotionSounds(count) {
  if (!state.motionSoundEnabled || count <= 0) return;
  for (let index = 0; index < count; index += 1) {
    const sound = state.motionSound.cloneNode();
    const release = () => {
      state.activeMotionSounds.delete(sound);
    };
    state.activeMotionSounds.add(sound);
    sound.addEventListener("ended", release, { once: true });
    sound.addEventListener("error", release, { once: true });
    sound.currentTime = 0;
    sound.play().catch(release);
  }
}

function stopMotionSounds() {
  state.activeMotionSounds.forEach((sound) => {
    sound.pause();
    sound.currentTime = 0;
  });
  state.activeMotionSounds.clear();
}

function resetMotionSoundState() {
  state.motionBoxCount = 0;
  stopMotionSounds();
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
    .catch(() => {
      ui.motionOn.checked = !enabled;
      syncMotionSound();
    })
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
