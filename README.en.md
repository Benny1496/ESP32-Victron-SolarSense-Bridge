# ESP32 Victron SolarSense Bridge – English

[Deutsch](README.de.md) · [**English**](README.en.md) · [Bilingual homepage](README.md)

This is an open-source ESP32/ESPHome community project based on a privately operated **stage 4.3.1**. Two Victron SolarSense BLE sensors provide measurements to Home Assistant. Their original BLE advertisements can also be forwarded via certificate-verified HTTPS to Cerbo GX (Venus OS).

## Current scope

- **Two** explicitly configured BLE sensors; support for additional sensors is a community roadmap item.
- Irradiance, estimated PV power, daily yield, cell temperature, RSSI, diagnostic data and ESPHome Bluetooth proxy support.
- Cerbo GX pairing and BLE forwarding to `/ble-gw/`; forwarding defaults **OFF** after a restart.
- HTTPS certificate/hostname verification with redirects disabled.
- A 15-second refresh for unchanged data instead of repeated identical transmissions.

## Test status

The original private stage 4.3.1 was observed working with two sensors. The publication source compiles completely under ESPHome 2026.9.1, and isolated C++ tests and automated privacy checks passed. The two new HTTPS/de-duplication changes **have not yet been tested together on actual Cerbo GX hardware**. This is **community source code**, not production-certified firmware.

## Getting started and documentation

| Topic | Deutsch | English |
|---|---|---|
| Installation | [Anleitung](docs/INSTALLATION.de.md) | [Guide](docs/INSTALLATION.en.md) |
| Home Assistant names | [Anzeigen](docs/HOME_ASSISTANT.de.md) | [Labels](docs/HOME_ASSISTANT.en.md) |
| Security | [Sicherheit](docs/SECURITY.de.md) | [Security](docs/SECURITY.en.md) |
| Transmission | [Übertragung](docs/TRANSMISSION.de.md) | [Transmission](docs/TRANSMISSION.en.md) |
| Development status | [Status](docs/STATUS.de.md) | [Status](docs/STATUS.en.md) |
| Credits and licensing | [Herkunft](docs/CREDITS.de.md) | [Credits](docs/CREDITS.en.md) |
| Contributing | [Beitragen](docs/CONTRIBUTING.de.md) | [Contributing](docs/CONTRIBUTING.en.md) |
| Publishing | [Hinweise](docs/PUBLISHING.de.md) | [Publishing](docs/PUBLISHING.en.md) |
| Release checks | [Checkliste](docs/RELEASE_CHECKLIST.de.md) | [Checklist](docs/RELEASE_CHECKLIST.md) |

The source is under `esphome/`. Private `secrets.yaml` and site-specific certificates must **never** be committed. Original project contributions use **GPL-3.0-only**; third-party rights remain applicable. This is not an official Victron, ESPHome or Shelly release.
