## Technical description

This project contains a firmware for ESP32-D0WDQ6 development board
It establishes WiFi using local credentials from `firmware/wifi_credentials.h`.
Copy `firmware/wifi_credentials.example.h` to `firmware/wifi_credentials.h` and fill in a 2.4 GHz WiFi network before flashing.
For controlling pin signal will be used pin 16.
The pin is normally high impedance. To toggle the lamp, firmware pulls it to ground for 100 ms and then releases it again.

When this firmware is started, it listens for UDP packets on port 4210.
Consumer can send these signals:

```text
on:5000
off
```

`on:5000` toggles the lamp immediately and toggles it again after 5000 ms.
`on` uses the default 5000 ms duration.
`off` cancels the pending timer and toggles the lamp off if the firmware believes it is currently on.
