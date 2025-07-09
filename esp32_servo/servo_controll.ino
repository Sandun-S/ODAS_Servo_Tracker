#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

#define PAN_PIN 18
#define TILT_PIN 19

//echo -n "AZ 0 EL 0" | nc -u 192.168.137.139 4210

IPAddress local_IP(192, 168, 4, 21);  // 👈 Your desired IP
IPAddress gateway(192, 168, 4, 1);     // Usually your router
IPAddress subnet(255, 255, 255, 0);

const char* ssid = "RPI-ESP32-HOTSPOT";
const char* password = "12345678";
// const char* ssid = "SLT-Syntax";
// const char* password = "0123456789";

WiFiUDP udp;
const unsigned int localUdpPort = 4210;
char incomingPacket[255];

Servo panServo;
Servo tiltServo;

void setup() {
  Serial.begin(115200);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");
  Serial.print("IP: "); Serial.println(WiFi.localIP());

  // Start UDP
  udp.begin(localUdpPort);
  Serial.printf("📡 Listening UDP on port %d\n", localUdpPort);

  // Servo setup
  panServo.setPeriodHertz(50);
  tiltServo.setPeriodHertz(50);
  panServo.attach(PAN_PIN, 500, 2400);
  tiltServo.attach(TILT_PIN, 500, 2400);

  moveServos(0, 0);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = '\0';
    processInput(String(incomingPacket));
  }
}

void processInput(String input) {
  input.trim();
  float az = 0, el = 0;

  int azPos = input.indexOf("AZ");
  int elPos = input.indexOf("EL");

  if (azPos != -1 && elPos != -1) {
    az = input.substring(azPos + 2, elPos).toFloat();
    el = input.substring(elPos + 2).toFloat();
    moveServos(az, el);
  }
}

void moveServos(float az, float el) {
  az = fmod(az, 360);
  if (az < 0) az += 360;

  float pan, tilt;
  if (az <= 180) {
    pan = az;
    tilt = constrain(el, 0, 90);
  } else {
    pan = az - 180;
    tilt = 180 - constrain(el, 0, 90);
  }

  pan = constrain(pan, 0, 180);
  tilt = constrain(tilt, 0, 180);

  panServo.write(pan);
  tiltServo.write(tilt);

  Serial.printf("📍 Pan: %.1f | Tilt: %.1f\n", pan, tilt);
}
