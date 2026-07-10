#include <WiFi.h>
#include <WiFiUdp.h>
#include "wifi_credentials.h"

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;

const int controlPin = 16;
const bool activeLow = true;
const unsigned int udpPort = 4210;
const unsigned long defaultOnSeconds = 5;
const unsigned long maxOnSeconds = 60;

WiFiUDP udp;
bool outputOn = false;
unsigned long offAtMs = 0;
unsigned long lastWifiRetryMs = 0;

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

void writeOutput(bool on)
{
  digitalWrite(controlPin, activeLow ? !on : on);
  outputOn = on;
  if (!on)
  {
    offAtMs = 0;
  }
}

void startOutput(unsigned long seconds)
{
  seconds = min(max(seconds, 1UL), maxOnSeconds);
  writeOutput(true);
  offAtMs = millis() + seconds * 1000UL;
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
  if (!packetSize)
  {
    return "";
  }

  char buffer[32];
  int length = udp.read(buffer, sizeof(buffer) - 1);
  if (length < 0)
  {
    return "";
  }

  buffer[length] = '\0';
  String command(buffer);
  command.trim();
  command.toLowerCase();
  return command;
}

bool parseOnSeconds(const String &command, unsigned long &seconds)
{
  if (command == "on")
  {
    seconds = defaultOnSeconds;
    return true;
  }

  if (!command.startsWith("on:"))
  {
    return false;
  }

  long parsed = command.substring(3).toInt();
  if (parsed <= 0)
  {
    return false;
  }

  seconds = min((unsigned long)parsed, maxOnSeconds);
  return true;
}

void handleCommand(const String &command)
{
  if (!command.length())
  {
    return;
  }

  if (command == "off")
  {
    writeOutput(false);
    sendReply("ok off");
    return;
  }

  unsigned long seconds = defaultOnSeconds;
  if (parseOnSeconds(command, seconds))
  {
    startOutput(seconds);
    sendReply("ok on:" + String(seconds));
    return;
  }

  sendReply("error expected on:seconds or off");
}

void maintainTimer()
{
  if (outputOn && (long)(millis() - offAtMs) >= 0)
  {
    writeOutput(false);
  }
}

void maintainWifi()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    return;
  }

  unsigned long now = millis();
  if (now - lastWifiRetryMs < 5000)
  {
    return;
  }

  lastWifiRetryMs = now;
  WiFi.disconnect();
  WiFi.begin(ssid, password);
}

void setup()
{
  Serial.begin(115200);
  delay(500);

  pinMode(controlPin, OUTPUT);
  writeOutput(false);

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
  Serial.print("UDP motor control on ");
  Serial.print(WiFi.localIP());
  Serial.print(":");
  Serial.println(udpPort);

  udp.begin(udpPort);
}

void loop()
{
  maintainWifi();
  handleCommand(readCommand());
  maintainTimer();
  delay(1);
}
