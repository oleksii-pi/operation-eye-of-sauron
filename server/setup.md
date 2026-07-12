This application represents a set of tools that manage:

1. Web Cam
   Tapo TP-Link C220
   360° WiFi Indoor Surveillance Camera, 2K 4MP, IR Night Vision, Motion Detection, Two-Way Audio, Compatible with Alexa and Google Assistant, for Babies/Pets

2. Host computer
   Mac
   Purpose: main control node that reads the camera stream,
   detects motion in real time,
   moves the camera toward the target,
   and sends UDP commands to the light controller.

3. LED light controller
   ESP32-D0WDQ6 development board
   Purpose: receive UDP `on:<duration-ms>` and `off` commands
   and pulse the connected LED output.
