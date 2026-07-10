loadLimits();
loadMotorAddress();
loadMotionSound();
centerDirection();
bindEvents();
ui.streamImage.src = streamUrl;
loadStatus();
updateLatency();
setInterval(updateLatency, 1000);
