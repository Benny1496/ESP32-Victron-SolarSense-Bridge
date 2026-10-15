# Ursprünglicher Sensor-Prototyp (historisch, Deutsch)

[Deutsch](PROTOTYPE.de.md) · [English](PROTOTYPE.en.md) · [Aktuelle Startseite](../README.md)

> **Historischer Entwicklungsstand:** Diese Seite dokumentiert den älteren, unabhängigen Multi-Sensor-C++-Prototyp. Sie beschreibt **nicht** die aktuelle funktionsfähige Zwei-Sensor-ESPHome-Vorlage aus `esphome/`.

## Ziel des früheren Prototyps

Der eigenständige Entwurf sollte eine **konfigurierbare Anzahl** von Victron SolarSense BLE-Sensoren verwalten können, statt sich auf zwei feste Dachseiten zu beschränken. Das war ein Entwicklungsziel und **keine** bereits getestete Produktivfunktion. Wie viele Sensoren zuverlässig möglich sind, hängt von ESP32-Speicher, BLE-Empfang, Netzwerk und Cerbo-GX-Eigenschaften ab.

Weitere Ziele: Originale BLE-Werbepakete unverändert aufbewahren; SolarSense-Herstellerdaten für Home Assistant dekodieren (Bestrahlungsstärke, geschätzte PV-Leistung, Tagesertrag, Zelltemperatur); RSSI und Diagnosewerte je Sensor erfassen; echte Zugangsdaten nie ins Repository aufnehmen.

## Bestandteile

- `src/solarsense_decoder.h`: eigenständiger C++17-Dekoder mit Behandlung ungültiger Datenfelder.
- `src/sensor_registry.h`: Sensorliste mit variabler Anzahl und Erhalt originaler Advertising-Bytes.
- `tests/test_solarsense.cpp`: Offline-Tests mit künstlichen Paketen.
- `examples/sensors.example.yaml`: **nur schematisches Beispiel**, kein direkt lauffähiges ESPHome-Modul.
- `docs/SOURCES.de.md`: Herkunft und Einordnung; vollständige Credits unter `docs/CREDITS.de.md`.

### Eigenständige Tests

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -Isrc \
  tests/test_solarsense.cpp -o /tmp/test_solarsense
/tmp/test_solarsense
```

## Bewusste Grenzen des früheren Entwurfs

Der Prototyp erzeugt keine ESPHome-Entitäten für beliebig viele Sensoren, keine vollständige generische GX-HTTPS-Transportpipeline und keine sichere Kopplung. Er enthält keine Hardwaretests für mehr als zwei Sensoren.

**Aktueller Stand:** Die veröffentlichte, auf 4.3.1 basierende Vorlage liegt in [`esphome/`](../esphome/README.md) und wurde mit zwei Sensoren entwickelt. Sie kompiliert in GitHub Actions; die neuen TLS-/Doppelsendungsänderungen sind noch nicht zusammen auf Cerbo-Hardware getestet. Für die aktuelle Einrichtung siehe [Installation (DE)](INSTALLATION.de.md).

Der frühere englische README-Text ist unverändert unter [PROTOTYPE.en.md](PROTOTYPE.en.md) archiviert. Dieses Projekt hat inzwischen eine GPL-3.0-only-Lizenz für eigene Bestandteile; die historische Aussage zur damals offenen Lizenzentscheidung gilt deshalb nur für diesen alten Entwurfsstand.
