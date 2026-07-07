## Technical description

This project contains a firmware for ESP32-D0WDQ6 development board
It should establish wifi connection using secured cridentials from .env
For controlling pin signal will be used pin 16

When this firmware is started, it listens HTTP on port 80
Consumer can send these signals:
GET http://192.168.0.231/on
GET http://192.168.0.231/off
