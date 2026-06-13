# Firmware — RFID Enrollment Scanner (ESP32)

A low-cost station used **during student enrollment** to read an RFID card's UID and display it on a 16×2 LCD. The operator copies the UID into the dashboard when enrolling a student. "Read the UID, show it, nothing more — but do it fast, well, and reliably."

## Role in the system

```
USB 5V ──► [ ESP32 DevKit ] ─ SPI ─► [ MFRC522 RFID ]
                 │   │
                 │   └─ I²C ─► [ 16×2 LCD @ 0x27 ]
                 │
                 └─► status LED + buzzer (GPIO)
```

The card UID is read at < 5 cm and shown in < 250 ms, with LED + buzzer feedback. Wi-Fi/Bluetooth are disabled in firmware to cut power draw and RF interference.

## Hardware

| Component | Interface | Pins (BCM/ESP32 GPIO) |
|---|---|---|
| MFRC522 RFID (13.56 MHz) | SPI | SS 5, SCK 18, MOSI 23, MISO 19, RST 22 |
| 16×2 LCD (PCF8574) | I²C | SDA 21, SCL 22 (addr `0x27`) |
| Status LED | GPIO | 6 |
| Buzzer | GPIO | 4 |

Full schematic, KiCad project, and 3D enclosure are documented in [docs/HARDWARE.md](../docs/HARDWARE.md). PCB sources live in [`rfid_reader/`](rfid_reader/) (`*.kicad_pro`, `*.kicad_sch`, `*.kicad_pcb`).

## Firmware

`firmware/firmware.ino` implements the scanner: it disables Wi-Fi/Bluetooth, polls
the MFRC522, formats each card UID as an uppercase colon-separated hex string,
shows it on the LCD, and gives LED + buzzer feedback. A simple change-detection
guard avoids re-triggering while a card is left on the reader.

## Build & flash

1. Open `firmware/` in the Arduino IDE or PlatformIO.
2. Install libraries: `MFRC522`, `LiquidCrystal_I2C`.
3. Select your ESP32 board and port, then upload.

## Pilot results

From the pilot deployment: **99.87%** successful reads over **783** card passes, ~120 ms display latency, peak USB draw ~310 mA.
