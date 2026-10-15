# ESP32 Victron SolarSense Bridge – Deutsch

Open-Source-Projekt aus einer tatsächlich betriebenen ESPHome-/ESP32-Installation: Zwei Victron SolarSense BLE-Sensoren werden in Home Assistant ausgewertet und ihre Original-Bluetooth-Werbepakete an einen Cerbo GX (Venus OS) weitergeleitet.

**Stand: Community-Quellcode-Vorschau, nicht als fertig getestetes Installationspaket freigegeben.** Die bewährte Ausgangsversion 4.3.1 wurde im Live-System mit zwei Sensoren über Nacht erfolgreich betrieben. Die hier angebotene Variante ersetzt private Gerätewerte durch eigene Einstellungen und ergänzt Zertifikatsprüfung sowie Erkennung unveränderter Daten. **Diese beiden Änderungen sind noch nicht im produktiven System getestet.**

Die englische `README.md` im Repository bleibt bewusst im bisherigen Zustand. Aktueller Einstieg in beide Sprachen:

- Installation: [Deutsch](docs/INSTALLATION.de.md) · [English](docs/INSTALLATION.en.md)
- Sicherheit: [Deutsch](docs/SECURITY.de.md) · [English](docs/SECURITY.en.md)
- Versandlogik: [Deutsch](docs/TRANSMISSION.de.md) · [English](docs/TRANSMISSION.en.md)
- Herkunft und Autoren: [Deutsch](docs/CREDITS.de.md) · [English](docs/CREDITS.en.md)
- Mitmachen: [Deutsch](docs/CONTRIBUTING.de.md) · [English](docs/CONTRIBUTING.en.md)
- Versions- und Teststand: [Deutsch](docs/STATUS.de.md) · [English](docs/STATUS.en.md)

Die Vorlage liegt unter `esphome/`. Eigene Zugangsdaten, MAC-Adressen, lokale Zertifikate und Gerätekonfigurationen gehören niemals in Git. Keine offizielle Veröffentlichung von Victron Energy, Shelly oder ESPHome. Eigene Codeanteile stehen unter GPL-3.0-only; Fremdrechte bleiben unberührt.

- Veröffentlichung / Publishing: [Deutsch](docs/PUBLISHING.de.md) · [English](docs/PUBLISHING.en.md)
