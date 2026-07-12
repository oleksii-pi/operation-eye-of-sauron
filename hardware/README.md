## Technical description

This project contains firmware for an ESP32-D0WDQ6 LED light controller.
It establishes WiFi using local credentials from `firmware/wifi_credentials.h`.
Copy `firmware/wifi_credentials.example.h` to `firmware/wifi_credentials.h` and fill in a 2.4 GHz WiFi network before uploading the firmware.
Pin 16 is used as the control output.
The pin is normally high impedance. To pulse the light, the firmware pulls it to ground for 100 ms and then releases it again.

When this firmware starts, it listens for UDP packets on port 4210.
The host application can send these signals:

```text
on:5000
off
```

`on:5000` toggles the light immediately and toggles it again after 5000 ms.
`on` uses the default 5000 ms duration.
`off` cancels the pending timer and toggles the light off if the firmware believes it is currently on.
