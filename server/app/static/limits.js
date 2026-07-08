function limitValue(input, fallback) {
  return input.value.trim() === "" ? fallback : clamp(input.value);
}

function cleanLimit(input) {
  if (input.value.trim() === "") return;
  input.value = clamp(input.value);
}

function loadLimits() {
  try {
    const limits = JSON.parse(localStorage.getItem(limitStorageKey) || "{}");
    limitInputs.forEach((input) => {
      if (Number.isFinite(Number(limits[input.id]))) input.value = limits[input.id];
    });
  } catch {
    localStorage.removeItem(limitStorageKey);
  }
}

function saveLimits() {
  const limits = {};
  limitInputs.forEach((input) => {
    if (input.value.trim() !== "") limits[input.id] = Number(input.value);
  });
  localStorage.setItem(limitStorageKey, JSON.stringify(limits));
}

function normalizeLimits(changedId = "") {
  cleanLimit(ui.minH);
  cleanLimit(ui.maxH);
  cleanLimit(ui.minV);
  cleanLimit(ui.maxV);
  if (ui.minH.value !== "" && ui.maxH.value !== "" && Number(ui.minH.value) > Number(ui.maxH.value)) {
    if (changedId === "minH") ui.maxH.value = ui.minH.value;
    else ui.minH.value = ui.maxH.value;
  }
  if (ui.minV.value !== "" && ui.maxV.value !== "" && Number(ui.minV.value) > Number(ui.maxV.value)) {
    if (changedId === "minV") ui.maxV.value = ui.minV.value;
    else ui.minV.value = ui.maxV.value;
  }
  ui.horizontal.min = limitValue(ui.minH, -100);
  ui.horizontal.max = limitValue(ui.maxH, 100);
  ui.vertical.min = limitValue(ui.minV, -100);
  ui.vertical.max = limitValue(ui.maxV, 100);
}

function clampHorizontal(value) {
  return clamp(value, limitValue(ui.minH, -100), limitValue(ui.maxH, 100));
}

function clampVertical(value) {
  return clamp(value, limitValue(ui.minV, -100), limitValue(ui.maxV, 100));
}

function applyLimits(send = false, changedId = "") {
  normalizeLimits(changedId);
  saveLimits();
  const nextHorizontal = clampHorizontal(ui.horizontal.value);
  const nextVertical = clampVertical(ui.vertical.value);
  const changed = nextHorizontal !== Number(ui.horizontal.value) || nextVertical !== Number(ui.vertical.value);
  ui.horizontal.value = nextHorizontal;
  ui.vertical.value = nextVertical;
  renderValues();
  if (changed && send) postDirection();
}

function followPayload() {
  const payload = {
    lag_ms: state.streamLagMs,
    max_adjustments: Number(ui.followSteps.value),
  };
  if (ui.minH.value.trim() !== "") payload.min_h = Number(ui.minH.value);
  if (ui.maxH.value.trim() !== "") payload.max_h = Number(ui.maxH.value);
  if (ui.minV.value.trim() !== "") payload.min_v = Number(ui.minV.value);
  if (ui.maxV.value.trim() !== "") payload.max_v = Number(ui.maxV.value);
  return payload;
}
