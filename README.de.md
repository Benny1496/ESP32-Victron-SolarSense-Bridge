# ESP32 Victron SolarSense Bridge – Deutsch

[**Deutsch**](README.de.md) · [English](README.en.md) · [Zweisprachige Startseite](README.md)

Dies ist ein Open-Source-ESP32-/ESPHome-Projekt auf Grundlage einer privat betriebenen **Stufe 4.3.1**. Zwei Victron SolarSense BLE-Sensoren werden in Home Assistant ausgewertet. Ihre originalen BLE-Werbepakete können zusätzlich über zertifikatsgeprüftes HTTPS an Cerbo GX (Venus OS) gesendet werden.

## Aktueller Umfang

- **Zwei** fest konfigurierte BLE-Sensoren; weitere Sensoren sind eine geplante Community-Erweiterung.
- Bestrahlungsstärke, geschätzte Leistung, Tagesertrag, Zelltemperatur, RSSI, Diagnosewerte und ESPHome-Bluetooth-Proxy.
- Cerbo-GX-Kopplung und BLE-Weiterleitung über `/ble-gw/`; nach Neustart ist die Übertragung **AUS**.
- HTTPS mit Zertifikats-/Hostnamenprüfung und Deaktivierung von Redirects.
- Bei identischen Daten 15-Sekunden-Refresh statt dauernder Doppelübertragungen.

## Teststand

Die originale private 4.3.1 war mit zwei Sensoren im Live-System funktionsfähig. Die veröffentlichte Variante wurde mit ESPHome 2026.9.1 vollständig kompiliert; die C++-Tests und die automatische Datenschutzprüfung waren erfolgreich. Die beiden neuen HTTPS-/Duplikatänderungen wurden **noch nicht gemeinsam auf echter Hardware mit einem Cerbo GX** getestet. Dies ist **Community-Quellcode**, keine produktiv zertifizierte Firmware.

## Einstieg und Dokumentation

| Thema | Deutsch | Englisch |
|---|---|---|
| Installation | [Anleitung](docs/INSTALLATION.de.md) | [Guide](docs/INSTALLATION.en.md) |
| Home-Assistant-Namen | [Anzeigen](docs/HOME_ASSISTANT.de.md) | [Labels](docs/HOME_ASSISTANT.en.md) |
| Sicherheit | [Sicherheit](docs/SECURITY.de.md) | [Security](docs/SECURITY.en.md) |
| Weiterleitung | [Übertragung](docs/TRANSMISSION.de.md) | [Transmission](docs/TRANSMISSION.en.md) |
| Entwicklungsstand | [Status](docs/STATUS.de.md) | [Status](docs/STATUS.en.md) |
| Quellen und Autoren | [Herkunft](docs/CREDITS.de.md) | [Credits](docs/CREDITS.en.md) |
| Mitmachen | [Beitragen](docs/CONTRIBUTING.de.md) | [Contributing](docs/CONTRIBUTING.en.md) |
| Veröffentlichung | [Hinweise](docs/PUBLISHING.de.md) | [Publishing](docs/PUBLISHING.en.md) |
| Prüfungen | [Checkliste](docs/RELEASE_CHECKLIST.de.md) | [Checklist](docs/RELEASE_CHECKLIST.md) |

Der Quellcode liegt unter `esphome/`; eine private `secrets.yaml` und eigene Vertrauenszertifikate werden **nicht** veröffentlicht. Die eigenen Anteile stehen unter **GPL-3.0-only**; Rechte Dritter bleiben bestehen. Keine offizielle Victron-/ESPHome-/Shelly-Veröffentlichung.
