# Home Assistant labels and translations (English)

[Deutsch](HOME_ASSISTANT.de.md) · [English](HOME_ASSISTANT.en.md) · [Home](../README.md)

## Why are some Home Assistant entities named in German?

The published ESPHome configuration is derived from live-tested stage 4.3.1. Existing German display names and source identifiers were intentionally preserved rather than renamed, to reduce the risk of breaking entity IDs, automations or dashboards. **Documentation is available in both languages; automatic runtime localization in Home Assistant is not implemented.**

| Existing German entity label | English meaning |
|---|---|
| Victron Bridge mit Cerbo koppeln | Pair Victron Bridge with Cerbo |
| Victron Bridge Übertragung aktiv | Victron Bridge forwarding enabled |
| Victron Bridge BLE-Pakete jetzt senden | Send Victron Bridge BLE packets now |
| Victron Bridge Cerbo HTTPS Verbindung testen | Test Cerbo HTTPS connection |
| Victron Bridge erfolgreiche Übertragungen | Successful transmissions |
| Victron Bridge Übertragungsfehler | Transmission errors |
| Victron Bridge Übertragungsstatus | Forwarding status |
| Victron Bridge Kopplungsstatus | Pairing status |
| SolarSense Südost | SolarSense Southeast (sensor 1) |
| SolarSense Nordwest | SolarSense Northwest (sensor 2) |
| Bestrahlungsstärke | Irradiance |
| Geschätzte Leistung | Estimated power |
| Heutiger Ertrag | Today's yield |
| Zelltemperatur | Cell temperature |
| Letzter Empfang | Last received packet |
| Letzte Sonne | Last sunlight |
| Gültige BLE-Pakete | Valid BLE packets |
| WLAN-Signal | Wi-Fi signal |
| Laufzeit | Uptime |

**Note:** “Südost” (southeast) and “Nordwest” (northwest) are historical names for the two example sensors, **not real published addresses or automatically detected roof orientations**. You can customize **friendly names in Home Assistant** to English. Avoid casually changing internal ESPHome IDs, which may be referenced by automations and code.

[Installation](INSTALLATION.en.md) · [Development status](STATUS.en.md)
