#include <WiFi.h>
#include <WiFiUdp.h>
#include "wifi_credentials.h"

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;

const int switchPin = 16;
const unsigned int udpPort = 4210;
const unsigned long defaultOnMs = 5000, maxOnMs = 600000, pressMs = 100;

WiFiUDP udp;
bool lampOn = false;
bool toggleScheduled = false;
unsigned long toggleAtMs = 0, lastWifiRetryMs = 0;

const char *wifiStatusName(wl_status_t status)
{
  switch (status)
  {
    case WL_IDLE_STATUS: return "idle";
    case WL_NO_SSID_AVAIL: return "ssid not found";
    case WL_SCAN_COMPLETED: return "scan complete";
    case WL_CONNECTED: return "connected";
    case WL_CONNECT_FAILED: return "connect failed";
    case WL_CONNECTION_LOST: return "connection lost";
    case WL_DISCONNECTED: return "disconnected";
    default: return "unknown";
  }
}

void releaseSwitch() { pinMode(switchPin, INPUT); }

void pressSwitch()
{
  pinMode(switchPin, OUTPUT);
  digitalWrite(switchPin, LOW);
  delay(pressMs);
  releaseSwitch();
  lampOn = !lampOn;
}

void scheduleToggle(unsigned long durationMs)
{
  durationMs = min(max(durationMs, 1UL), maxOnMs);
  pressSwitch();
  toggleScheduled = true;
  toggleAtMs = millis() + durationMs;
}

void turnLampOff()
{
  toggleScheduled = false;
  toggleAtMs = 0;
  if (lampOn) pressSwitch();
}

void sendReply(const String &message)
{
  udp.beginPacket(udp.remoteIP(), udp.remotePort());
  udp.print(message);
  udp.endPacket();
}

String readCommand()
{
  int packetSize = udp.parsePacket();
  if (!packetSize) return "";

  char buffer[32];
  int length = udp.read(buffer, sizeof(buffer) - 1);
  if (length < 0) return "";

  buffer[length] = '\0';
  String command(buffer);
  command.trim();
  command.toLowerCase();
  return command;
}

bool parseOnMs(const String &command, unsigned long &durationMs)
{
  if (command == "on")
  {
    durationMs = defaultOnMs;
    return true;
  }
  if (!command.startsWith("on:")) return false;

  long parsed = command.substring(3).toInt();
  if (parsed <= 0) return false;

  durationMs = min((unsigned long)parsed, maxOnMs);
  return true;
}

void handleCommand(const String &command)
{
  if (!command.length()) return;

  if (command == "off")
  {
    turnLampOff();
    sendReply("ok off");
    return;
  }

  unsigned long durationMs = defaultOnMs;
  if (parseOnMs(command, durationMs))
  {
    scheduleToggle(durationMs);
    sendReply("ok on:" + String(durationMs));
    return;
  }

  sendReply("error expected on:milliseconds or off");
}

void maintainToggle()
{
  if (toggleScheduled && (long)(millis() - toggleAtMs) >= 0)
  {
    toggleScheduled = false;
    toggleAtMs = 0;
    pressSwitch();
  }
}

void maintainWifi()
{
  if (WiFi.status() == WL_CONNECTED) return;

  unsigned long now = millis();
  if (now - lastWifiRetryMs < 5000) return;

  lastWifiRetryMs = now;
  WiFi.disconnect();
  WiFi.begin(ssid, password);
}

void setup()
{
  Serial.begin(115200);
  delay(500);

  releaseSwitch();

  WiFi.begin(ssid, password);

  Serial.println();
  Serial.print("Connecting to WiFi");
  unsigned long lastStatusMs = 0;
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(250);
    Serial.print(".");
    unsigned long now = millis();
    if (now - lastStatusMs >= 5000)
    {
      lastStatusMs = now;
      Serial.print(" ");
      Serial.print(wifiStatusName(WiFi.status()));
    }
  }

  Serial.println();
  Serial.print("UDP lamp control on ");
  Serial.print(WiFi.localIP());
  Serial.print(":");
  Serial.println(udpPort);

  udp.begin(udpPort);
}

void loop()
{
  maintainWifi();
  handleCommand(readCommand());
  maintainToggle();
  delay(1);
}
