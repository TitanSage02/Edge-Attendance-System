/*
 * RFID Enrollment Scanner — ESP32
 * Edge Attendance System (firmware-enrollment)
 *
 * Reads the UID of an RFID card presented to the MFRC522 (< 5 cm) and shows it
 * on a 16x2 I2C LCD with LED + buzzer feedback. The operator copies the UID
 * into the dashboard when enrolling a student. Wi-Fi/Bluetooth are disabled to
 * reduce power draw and RF interference.
 *
 * Hardware / wiring (ESP32 GPIO):
 *   MFRC522 (SPI): SS=5, SCK=18, MOSI=23, MISO=19, RST=22
 *   16x2 LCD (I2C, PCF8574 @ 0x27): SDA=21, SCL=22
 *   Status LED: GPIO 6
 *   Buzzer:     GPIO 4
 *
 * Libraries: MFRC522, LiquidCrystal_I2C
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <esp_bt.h>

// ---- Pin configuration ----
#define SS_PIN      5
#define RST_PIN     22
#define LED_PIN     6
#define BUZZER_PIN  4

// ---- LCD configuration ----
#define LCD_ADDR    0x27
#define LCD_COLS    16
#define LCD_ROWS    2

// ---- Behaviour ----
static const unsigned long LOOP_DELAY_MS = 50;  // poll period

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

String lastUID = "";

// Disable radios we do not use (lower power, fewer RF interferences).
void disableNetworkFeatures() {
  WiFi.mode(WIFI_OFF);
  btStop();
}

// Format the current card UID as an uppercase, colon-separated hex string.
String getCardUID() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += ":";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";  // zero-pad each byte
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void displayCardUID(const String &uid) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID:");
  lcd.setCursor(0, 1);
  lcd.print(uid);
}

void displayWaiting() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("En attente...");
}

void playCardDetectedSound() {
  tone(BUZZER_PIN, 1000, 100);  // 1 kHz, 100 ms
  digitalWrite(LED_PIN, HIGH);
}

void setup() {
  Serial.begin(115200);

  disableNetworkFeatures();

  // SPI + RFID
  SPI.begin();
  rfid.PCD_Init();

  // LCD
  lcd.init();
  lcd.backlight();

  // Feedback outputs
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  lcd.setCursor(0, 0);
  lcd.print("Scanner pret");
  delay(1000);
  displayWaiting();

  Serial.println("RFID enrollment scanner ready");
}

void loop() {
  // A new card is present and readable
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = getCardUID();

    // Only react when the UID changes (debounce a card left on the reader)
    if (uid != lastUID) {
      lastUID = uid;
      displayCardUID(uid);
      playCardDetectedSound();
      Serial.println("UID: " + uid);
    }

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  } else {
    // No card: return to idle once
    if (lastUID != "") {
      displayWaiting();
      digitalWrite(LED_PIN, LOW);
      lastUID = "";
    }
  }

  delay(LOOP_DELAY_MS);
}
