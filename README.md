# ESP32 Victron SolarSense Bridge

**🌐 Sprache / Language: [Deutsch](#deutsch) · [English](#english)**

> **Deutsch:** Offenes ESP32-/ESPHome-Projekt für zwei Victron SolarSense BLE-Sensoren, Home Assistant und einen Cerbo GX (Venus OS). Die Veröffentlichung basiert auf der im privaten Live-System bewährten Stufe 4.3.1. Zertifikatsgeprüftes HTTPS und die Vermeidung unnötiger Doppelübertragungen sind zusätzliche, noch nicht auf der echten Anlage gemeinsam erprobte Änderungen.
>
> **English:** Open-source ESP32/ESPHome project connecting two Victron SolarSense BLE sensors to Home Assistant and Cerbo GX (Venus OS). The source is based on privately operated stage 4.3.1. Verified HTTPS certificates and suppression of unnecessary duplicate transmissions are new changes, not yet jointly tested on the real installation.

---

<a id="deutsch"></a>
## 🇩🇪 Deutsch

### Was macht die Bridge?

- Empfängt die originalen Bluetooth-Werbepakete von **zwei konfigurierten SolarSense-Sensoren**.
- Stellt Bestrahlungsstärke, geschätzte PV-Leistung, Tagesertrag, Zelltemperatur, RSSI und Diagnosewerte in **Home Assistant** bereit.
- Behält die **ESPHome-Bluetooth-Proxy-Funktion** bei.
- Übermittelt die unveränderten BLE-Pakete über den Cerbo-GX-Endpunkt `/ble-gw/` per **HTTPS mit Zertifikatsprüfung**.
- Unterdrückt unveränderte BLE-Daten zwischen den Übertragungen; spätestens nach **15 Sekunden** erfolgt bei weiterhin gültigen Daten eine Auffrischung.
- Startet mit **ausgeschalteter Cerbo-Übertragung**. Die Kopplung und das Einschalten erfolgen bewusst über Home Assistant.

**Wichtig:** Dies ist eine **Community-Quellcode-Vorschau** und keine produktiv zertifizierte Firmware. Die ursprüngliche private 4.3.1 wurde mit zwei Sensoren beobachtet; die hier hinzugefügten HTTPS-/Duplikatänderungen wurden erfolgreich kompiliert und isoliert getestet, aber nicht zusammen auf einem realen Cerbo GX geprüft. Die aktuelle ESPHome-Vorlage unterstützt **zwei Sensoren**, nicht beliebig viele.

### Schnellstart

1. Lies die [deutsche Installationsanleitung](docs/INSTALLATION.de.md).
2. Verwende die Dateien aus `esphome/` in einem **separaten ESPHome-Testprojekt**.
3. Erstelle eine eigene, private `secrets.yaml` anhand von `esphome/secrets.example.yaml`. Verwende deine eigenen MAC-Adressen, Schlüssel, WLAN-Daten und Cerbo-URL.
4. Stelle ein vertrauenswürdiges **öffentliches CA-/Serverzertifikat** passend zum Cerbo-Hostnamen bereit. Zertifikatsprüfung niemals deaktivieren.
5. Validiere und kompiliere zuerst; prüfe Hardware und Pairing separat, bevor du die Übertragung aktivierst.

### Dokumentation auf Deutsch und Englisch

| Thema | Deutsch | English |
|---|---|---|
| Übersicht / Overview | [README.de.md](README.de.md) | [README.en.md](README.en.md) |
| Installation | [Installation](docs/INSTALLATION.de.md) | [Installation](docs/INSTALLATION.en.md) |
| Home-Assistant-Anzeigen | [Bezeichnungen](docs/HOME_ASSISTANT.de.md) | [Labels](docs/HOME_ASSISTANT.en.md) |
| Sicherheit & Privatsphäre | [Sicherheit](docs/SECURITY.de.md) | [Security](docs/SECURITY.en.md) |
| BLE-Datenweiterleitung | [Übertragung](docs/TRANSMISSION.de.md) | [Transmission](docs/TRANSMISSION.en.md) |
| Test- und Entwicklungsstand | [Status](docs/STATUS.de.md) | [Status](docs/STATUS.en.md) |
| Urheber & Lizenzen | [Quellen](docs/CREDITS.de.md) | [Credits](docs/CREDITS.en.md) |
| Mitmachen | [Beitragen](docs/CONTRIBUTING.de.md) | [Contributing](docs/CONTRIBUTING.en.md) |
| Veröffentlichung | [Veröffentlichung](docs/PUBLISHING.de.md) | [Publishing](docs/PUBLISHING.en.md) |
| Prüf-Checkliste | [Checkliste](docs/RELEASE_CHECKLIST.de.md) | [Checklist](docs/RELEASE_CHECKLIST.md) |
| Dokumentenindex | [Übersicht](docs/README.md#deutsch) | [Index](docs/README.md#english) |

**Lizenz:** Eigene Projektanteile unter GPL-3.0-only; fremde Rechte und Lizenzhinweise beachten. Siehe [LICENSE](LICENSE) und [Quellenhinweise](docs/CREDITS.de.md). Unabhängiges Community-Projekt, nicht offiziell von Victron, ESPHome oder Shelly.

---

<a id="english"></a>
## 🇬🇧 English

### What does the bridge do?

- Captures original Bluetooth advertisements from **two configured SolarSense sensors**.
- Exposes irradiance, estimated PV power, daily yield, cell temperature, RSSI and diagnostics in **Home Assistant**.
- Preserves the **ESPHome Bluetooth proxy** functionality.
- Forwards unmodified BLE advertisements to the Cerbo GX `/ble-gw/` endpoint via **certificate-verified HTTPS**.
- Avoids duplicate transmissions of unchanged BLE data, with a periodic **15-second** refresh while input data remains valid.
- Keeps Cerbo forwarding **OFF after reboot**. Pairing and forwarding are explicitly controlled in Home Assistant.

**Important:** This is a **community source preview**, not production-certified firmware. The private stage 4.3.1 worked with two sensors; the new HTTPS and duplicate-suppression changes compile and pass isolated tests but have not been validated together against an actual Cerbo GX. The current ESPHome template supports **two sensors**, not an arbitrary number.

### Quick start

1. Read the [English installation guide](docs/INSTALLATION.en.md).
2. Copy `esphome/` into a **separate ESPHome test project**.
3. Create your own private `secrets.yaml` from `esphome/secrets.example.yaml`; supply your own MACs, keys, Wi-Fi settings and Cerbo URL.
4. Provide a trusted **public CA/server certificate** matching the Cerbo hostname. Never bypass certificate verification.
5. Validate and compile first; test the actual hardware and pairing separately before enabling forwarding.

### Documentation

The table in the [German section above](#dokumentation-auf-deutsch-und-englisch) links **each topic in both languages**. For language-specific introductions see [README.de.md](README.de.md) and [README.en.md](README.en.md); for the full navigation see [Documentation index](docs/README.md).

**License:** Original contributions are licensed under GPL-3.0-only, without overriding third-party rights. See [LICENSE](LICENSE) and [credits](docs/CREDITS.en.md). Independent community project; not officially affiliated with or endorsed by Victron, ESPHome or Shelly.

### Verification / Prüfung

GitHub Actions builds the ESPHome 2026.9.1 firmware with **synthetic, temporary credentials** and runs standalone C++ and privacy checks. These passing tests **do not replace real-hardware integration testing**.

[Deutsch ↑](#deutsch) · [English ↑](#english)
