# Quellen und Projektstruktur (Deutsch)

[Deutsch](SOURCES.de.md) · [English](SOURCES.md) · [Dokumentation](README.md)

Ausführliche Angaben zu ursprünglichen Autoren, Codeherkunft, Lizenzgrenzen und fremden Rechten stehen unter [Herkunft und Autoren](CREDITS.de.md). Die englische Fassung ist [CREDITS.en.md](CREDITS.en.md).

## Welche Dateien sind wofür?

- **`esphome/`:** aktuelle öffentliche Zwei-Sensor-Vorlage, abgeleitet aus der privat getesteten Stufe 4.3.1. Sie enthält die ESPHome-Konfiguration und den HTTPS-Hintergrund-Worker.
- **`src/`, `tests/test_solarsense.cpp`, `examples/`:** ältere unabhängige Prototypen und synthetische Tests zur Dekodierung und variablen Sensorverwaltung. Das ist **nicht** dieselbe Implementierung wie die zurzeit installierbare Zwei-Sensor-ESPHome-Vorlage.
- **`tests/test_duplicate.cpp`:** isolierter Test der Übertragungs- und Auffrischungsentscheidung.
- **`docs/`:** deutsch- und englischsprachige Anleitungen. Die [zweisprachige Startseite](../README.md) enthält den aktuellen Stand.

Der alte englische `README.md`-Prototyptext wurde bei der zweisprachigen Umstellung am 15. Oktober 2026 durch eine aktuelle **deutsch-englische** Projektübersicht ersetzt und ist unter [PROTOTYPE.en.md](PROTOTYPE.en.md) archiviert. Eine deutsche Übersetzung des damaligen Entwicklungsstands steht unter [PROTOTYPE.de.md](PROTOTYPE.de.md). Die vollständige Firmware-Kompilierung in GitHub Actions war erfolgreich; die neuen TLS- und Duplikatfunktionen sind noch nicht zusammen auf echter Cerbo-Hardware getestet.
