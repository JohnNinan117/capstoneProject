/*****************************************************************
*  Two DS18B20s on A0 / A1
*  Six voltage taps on A2–A7
*  Four ACTIVE-LOW relays on D2–D5
*
*  Host command :  S,<id>,<0|1>\n
*                  id = 1–4 → relay index
*  MCU reply    :  ACK,<pin>,<0|1>\n
*  Telemetry    :  DATA,t1,t2,v1..v6\n
*****************************************************************/
#include <OneWire.h>
#include <DallasTemperature.h>
 
/* ───── pin map ─────────────────────────────────────────────── */
const uint8_t TEMP1_PIN = A0; // Batt sensor
const uint8_t TEMP2_PIN = A1; // Heater sensor
 
const uint8_t RELAY_PINS[4] = {2, 3, 4, 5};     // active-LOW relays
const uint8_t VOLT_PINS [6] = {A2, A3, A4, A5, A6, A7};
 
/* ───── constants ───────────────────────────────────────────── */
constexpr float    ADC_STEP  = 5.0f / 1023.0f;
constexpr float    DIV_RATIO = 5.0f;
constexpr uint32_t PUSH_MS   = 100;
constexpr uint16_t DS_DELAY  = 94;
 
/* ───── OneWire sensors ────────────────────────────────────── */
OneWire bus1(TEMP1_PIN);
OneWire bus2(TEMP2_PIN);
DallasTemperature ts1(&bus1);
DallasTemperature ts2(&bus2);
 
/* ───── helper ─────────────────────────────────────────────── */
inline void relayWrite(uint8_t pin, bool on) {
  digitalWrite(pin, on ? LOW : HIGH);
}
 
/* ───── setup ──────────────────────────────────────────────── */
void setup() {
  Serial.begin(115200);
 
  for (uint8_t p : RELAY_PINS) {
    pinMode(p, OUTPUT);
    relayWrite(p, false);  // Start OFF
  }
 
  ts1.begin();
  ts2.begin();
  ts1.setResolution(9);
  ts2.setResolution(9);
  ts1.setWaitForConversion(false);
  ts2.setWaitForConversion(false);
 
  pinMode(TEMP1_PIN, INPUT_PULLUP);  // A0
  pinMode(TEMP2_PIN, INPUT_PULLUP);  // A1
}
 
/* ───── main loop ──────────────────────────────────────────── */
void loop() {
  // 1 ─ Handle relay control commands
  while (Serial.available()) {
    if (Serial.peek() != 'S') {
      Serial.read(); continue;
    }
    if (Serial.read() != 'S') continue;
 
    int id = Serial.parseInt();   // 1–4
    int state = Serial.parseInt();
    Serial.read();                // Consume \n or \r
 
    if (id >= 1 && id <= 4) {
      uint8_t pin = RELAY_PINS[id - 1];
      relayWrite(pin, state);
      Serial.print(F("ACK,")); Serial.print(pin); Serial.print(','); Serial.println(state);
    }
  }
 
  // 2 ─ Read DS18B20 non-blocking
  static bool convBusy = false;
  static uint32_t tStart = 0;
  static float t1 = NAN, t2 = NAN;
  uint32_t now = millis();
 
  if (!convBusy) {
    ts1.requestTemperatures();
    ts2.requestTemperatures();
    convBusy = true;
    tStart = now;
  } else if (now - tStart >= DS_DELAY) {
    float temp1 = ts1.getTempCByIndex(0);
    float temp2 = ts2.getTempCByIndex(0);
 
    t1 = (temp1 == DEVICE_DISCONNECTED_C) ? NAN : temp1;
    t2 = (temp2 == DEVICE_DISCONNECTED_C) ? NAN : temp2;
    convBusy = false;
  }
 
  // 3 ─ Send telemetry every 100 ms
  static uint32_t lastPush = 0;
  if (now - lastPush >= PUSH_MS) {
    lastPush = now;
 
    float v[6];
    for (uint8_t i = 0; i < 6; ++i)
      v[i] = analogRead(VOLT_PINS[i]) * ADC_STEP * DIV_RATIO;
 
    Serial.print(F("DATA,"));
    Serial.print(isnan(t1) ? -99.99 : t1, 2); Serial.print(',');
    Serial.print(isnan(t2) ? -99.99 : t2, 2); Serial.print(',');
    for (uint8_t i = 0; i < 6; ++i) {
      Serial.print(v[i], 2);
      Serial.print(i < 5 ? ',' : '\n');
    }
  }
}
 
 