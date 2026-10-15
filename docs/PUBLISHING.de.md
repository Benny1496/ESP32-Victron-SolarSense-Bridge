# Veröffentlichung und Datenschutz (Deutsch)

[Deutsch](PUBLISHING.de.md) · [English](PUBLISHING.en.md) · [Startseite](../README.md)

## Aktueller öffentlicher Stand

Das Repository [ESP32-Victron-SolarSense-Bridge](https://github.com/Benny1496/ESP32-Victron-SolarSense-Bridge) ist **öffentlich**. Es enthält den geprüften Projektstand mit einem **neuen Git-Verlauf**. Der ursprüngliche private Entwicklungsstand mit dem aufgegebenen Alpha-Branch und dessen Pull Request befindet sich weiterhin in einem **separaten privaten Archiv**.

Die öffentliche Fassung verwendet eigene, private `secrets.yaml`-Dateien und ein vom jeweiligen Nutzer selbst zu beschaffendes TLS-Vertrauenszertifikat; es werden **keine echten Konfigurationswerte oder Zertifikate aus der ursprünglichen Anlage** veröffentlicht.

## Was bisher geprüft wurde

- Die übertragenen Quellcode-Dateien wurden auf bekannte interne IP-Adressen, persönliche Hardware-MACs und private Schlüssel überprüft. Der automatisierte Filter [`check_publication_privacy.py`](../scripts/check_publication_privacy.py) ergänzt die manuelle Kontrolle – **er ist keine Garantie**, alle denkbaren Geheimnisse zu erkennen.
- Der neue öffentliche Git-Verlauf enthält **keine früheren Alpha-Commits oder Pull Requests**.
- C++-Einzeltests, ESPHome-2026.9.1-Konfigurationsprüfung und **vollständige Firmware-Kompilierung** wurden mit künstlichen CI-Testwerten erfolgreich ausgeführt.
- Die bereits produktiv verwendete Stufe 4.3.1 ist nicht identisch mit der öffentlichen Vorlage: TLS-Zertifikatsprüfung und 15-Sekunden-Duplikat-Refresh sind Änderungen, die noch **nicht gemeinsam an echter Hardware** erprobt sind.

## Für künftige Änderungen

1. Beiträge in Deutsch **oder** Englisch sind willkommen. Bei neuen Funktionen möglichst **beide Sprachfassungen** aktualisieren.
2. Niemals lokale `secrets.yaml`, private Schlüssel, Tokens, MAC-Adressen, internen IPs oder Diagnose-Logs einchecken.
3. Vor einem Pull Request die automatischen Prüfungen durchführen und reale Hardwaretests als **getestet** oder **noch nicht getestet** kennzeichnen.
4. Es gibt einen automatischen sauberen Quellcode-Export über GitHub Actions. Dieser exportiert nur aktuelle Quelltextdateien, keine alte Commit-Historie.
5. Bei fremdem Code die Lizenz- und Urheberhinweise prüfen: [Quellen und Autoren](CREDITS.de.md).

Dieses Dokument beschreibt die **bereits erfolgte Veröffentlichung**, keine Aufforderung, das private Archiv öffentlich zu machen.
