## Technical description

This project contains a firmware for ESP32-D0WDQ6 development board
It establishes WiFi using local credentials from `firmware/wifi_credentials.h`.
Copy `firmware/wifi_credentials.example.h` to `firmware/wifi_credentials.h` and fill in a 2.4 GHz WiFi network before flashing.
For controlling pin signal will be used pin 16

When this firmware is started, it listens for UDP packets on port 4210.
Consumer can send these signals:

```text
on:5
off
```

`on:5` turns GPIO16 on for 5 seconds and then turns it off automatically.
`off` turns GPIO16 off immediately.
