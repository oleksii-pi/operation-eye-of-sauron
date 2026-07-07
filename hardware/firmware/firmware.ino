#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>

const char *ssid = "XXX";
const char *password = "XXX";

WebServer server(80);
Preferences preferences;

int controlPin = 16;   // Default GPIO
bool activeLow = true; // true for many relay modules

bool isAllowedOutputPin(int pin)
{
  // GPIO6-GPIO11 are connected to flash on most ESP32 boards
  if (pin >= 6 && pin <= 11)
    return false;

  // GPIO34-GPIO39 are input-only
  if (pin >= 34 && pin <= 39)
    return false;

  // Avoid negative or too high values
  if (pin < 0 || pin > 39)
    return false;

  // These are boot strapping pins. Better avoid for relay control.
  if (pin == 0 || pin == 2 || pin == 5 || pin == 12 || pin == 15)
    return false;

  return true;
}

void writeOutput(bool on)
{
  if (activeLow)
  {
    digitalWrite(controlPin, on ? LOW : HIGH);
  }
  else
  {
    digitalWrite(controlPin, on ? HIGH : LOW);
  }
}

void setupOutputPin()
{
  pinMode(controlPin, OUTPUT);
  writeOutput(false);
}

void loadConfig()
{
  preferences.begin("gpio-config", false);

  controlPin = preferences.getInt("pin", 16);
  activeLow = preferences.getBool("activeLow", true);

  if (!isAllowedOutputPin(controlPin))
  {
    controlPin = 16;
  }
}

void saveConfig()
{
  preferences.putInt("pin", controlPin);
  preferences.putBool("activeLow", activeLow);
}

void handleRoot()
{
  String html;

  html += "<h1>ESP32 GPIO Control</h1>";
  html += "<p>Current GPIO: <b>" + String(controlPin) + "</b></p>";
  html += "<p>Active low: <b>" + String(activeLow ? "yes" : "no") + "</b></p>";

  html += "<p><a href='/on'>ON</a></p>";
  html += "<p><a href='/off'>OFF</a></p>";

  html += "<hr>";
  html += "<h2>Configure</h2>";
  html += "<p>For GPIO16 active-low relay:</p>";
  html += "<p><a href='/config?pin=16&activeLow=1'>Set GPIO16 active-low</a></p>";

  html += "<p>For GPIO16 normal output:</p>";
  html += "<p><a href='/config?pin=16&activeLow=0'>Set GPIO16 normal</a></p>";

  html += "<p>Example safer relay pins:</p>";
  html += "<p><a href='/config?pin=25&activeLow=1'>GPIO25 active-low</a></p>";
  html += "<p><a href='/config?pin=26&activeLow=1'>GPIO26 active-low</a></p>";
  html += "<p><a href='/config?pin=27&activeLow=1'>GPIO27 active-low</a></p>";

  html += "<hr>";
  html += "<p>Manual format:</p>";
  html += "<code>/config?pin=16&activeLow=1</code>";

  server.send(200, "text/html", html);
}

void handleOn()
{
  writeOutput(true);
  server.send(200, "text/plain", "ON on GPIO" + String(controlPin));
}

void handleOff()
{
  writeOutput(false);
  server.send(200, "text/plain", "OFF on GPIO" + String(controlPin));
}

void handleStatus()
{
  String json = "{";
  json += "\"pin\":" + String(controlPin) + ",";
  json += "\"activeLow\":" + String(activeLow ? "true" : "false");
  json += "}";

  server.send(200, "application/json", json);
}

void handleConfig()
{
  if (!server.hasArg("pin"))
  {
    server.send(400, "text/plain", "Missing pin. Example: /config?pin=16&activeLow=1");
    return;
  }

  int newPin = server.arg("pin").toInt();

  if (!isAllowedOutputPin(newPin))
  {
    server.send(400, "text/plain", "Invalid or unsafe output GPIO");
    return;
  }

  writeOutput(false);

  controlPin = newPin;

  if (server.hasArg("activeLow"))
  {
    activeLow = server.arg("activeLow").toInt() == 1;
  }

  setupOutputPin();
  saveConfig();

  server.send(200, "text/plain",
              "Saved: GPIO" + String(controlPin) +
                  ", activeLow=" + String(activeLow ? "1" : "0"));
}

void setup()
{
  Serial.begin(115200);
  delay(500);

  loadConfig();
  setupOutputPin();

  WiFi.begin(ssid, password);

  Serial.println();
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("Open this address: http://");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/on", handleOn);
  server.on("/off", handleOff);
  server.on("/status", handleStatus);
  server.on("/config", handleConfig);

  server.begin();
  Serial.println("Web server started");
}

void loop()
{
  server.handleClient();
}