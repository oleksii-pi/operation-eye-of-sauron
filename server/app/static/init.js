loadLimits();
loadMotorAddress();
centerDirection();
bindEvents();
ui.streamImage.src = streamUrl;
loadStatus();
updateLatency();
setInterval(updateLatency, 2000);
