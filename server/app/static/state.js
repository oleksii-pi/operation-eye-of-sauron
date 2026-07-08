const ui = {
  horizontal: document.querySelector("#horizontal"),
  vertical: document.querySelector("#vertical"),
  minH: document.querySelector("#minH"),
  maxH: document.querySelector("#maxH"),
  minV: document.querySelector("#minV"),
  maxV: document.querySelector("#maxV"),
  motionOn: document.querySelector("#motionOn"),
  motionSize: document.querySelector("#motionSize"),
  horizontalValue: document.querySelector("#horizontalValue"),
  verticalValue: document.querySelector("#verticalValue"),
  motionSizeValue: document.querySelector("#motionSizeValue"),
  streamImage: document.querySelector("#streamImage"),
  follow: document.querySelector("#follow"),
  followSteps: document.querySelector("#followSteps"),
  followStatus: document.querySelector("#followStatus"),
  record: document.querySelector("#record"),
  recordStatus: document.querySelector("#recordStatus"),
  motorOn: document.querySelector("#motorOn"),
  motorStatus: document.querySelector("#motorStatus"),
  latencyValue: document.querySelector("#latencyValue"),
  latencyStart: document.querySelector("#latencyStart"),
};

const state = {
  sendTimer: 0,
  motionTimer: 0,
  isRecording: false,
  streamLagMs: 1000,
};

const streamUrl = "/stream.mjpg";
const limitStorageKey = "cameraLimits";
const limitInputs = [ui.minH, ui.maxH, ui.minV, ui.maxV];

function clamp(value, min = -100, max = 100) {
  return Math.max(min, Math.min(max, Number(value) || 0));
}

function clampSteps(value) {
  return Math.max(1, Math.min(5, Number(value) || 3));
}

function renderValues() {
  ui.horizontalValue.value = ui.horizontal.value;
  ui.verticalValue.value = ui.vertical.value;
  ui.motionSizeValue.value = ui.motionSize.value;
}
