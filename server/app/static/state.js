const ui = {
  horizontal: document.querySelector("#horizontal"),
  vertical: document.querySelector("#vertical"),
  minH: document.querySelector("#minH"),
  maxH: document.querySelector("#maxH"),
  minV: document.querySelector("#minV"),
  maxV: document.querySelector("#maxV"),
  motionOn: document.querySelector("#motionOn"),
  motionSoundRow: document.querySelector("#motionSoundRow"),
  motionSound: document.querySelector("#motionSound"),
  motionSize: document.querySelector("#motionSize"),
  motionSizeDown: document.querySelector("#motionSizeDown"),
  motionSizeUp: document.querySelector("#motionSizeUp"),
  horizontalValue: document.querySelector("#horizontalValue"),
  verticalValue: document.querySelector("#verticalValue"),
  motionSizeValue: document.querySelector("#motionSizeValue"),
  streamImage: document.querySelector("#streamImage"),
  record: document.querySelector("#record"),
  recordFps: document.querySelector("#recordFps"),
  recordStatus: document.querySelector("#recordStatus"),
  powerAddress: document.querySelector("#powerAddress"),
  powerOn: document.querySelector("#powerOn"),
  powerSeconds: document.querySelector("#powerSeconds"),
  powerStatus: document.querySelector("#powerStatus"),
  latencyValue: document.querySelector("#latencyValue"),
  latencyStart: document.querySelector("#latencyStart"),
};

const state = {
  sendTimer: 0,
  motionTimer: 0,
  isRecording: false,
  motionSoundEnabled: false,
  powerSecondsTouched: false,
  motionBoxCount: 0,
  activeMotionSounds: new Set(),
  motionSound: new Audio("/static/mouse-click.mp3"),
};

const streamUrl = "/stream.mjpg";
const limitStorageKey = "cameraLimits";
const powerAddressStorageKey = "powerUdpAddress";
const powerSecondsStorageKey = "powerSeconds";
const motionSoundStorageKey = "motionSoundEnabled";
const recordFpsStorageKey = "recordFps";
const limitInputs = [ui.minH, ui.maxH, ui.minV, ui.maxV];

function clamp(value, min = -100, max = 100) {
  return Math.max(min, Math.min(max, Number(value) || 0));
}

function renderValues() {
  ui.horizontalValue.value = ui.horizontal.value;
  ui.verticalValue.value = ui.vertical.value;
  ui.motionSizeValue.value = ui.motionSize.value;
}
