# Veröffentlichungs-Checkliste (Deutsch)

## Im aktuellen Quellcode erledigt

- [x] Produktive Stufe 4.3.1 als Grundlage und vorhandene Home-Assistant-/BLE-Logik behalten; kein Eingriff ins Live-System.
- [x] Konkrete Geräteadressen und private API-Schlüssel aus den veröffentlichten Beispielen entfernen.
- [x] Zertifikatsprüfung für HTTPS einschalten und Weiterleitungen deaktivieren.
- [x] Hintergrundübertragung erhalten; gleiche BLE-Daten bis zum zyklischen Refresh nicht unnötig erneut senden.
- [x] Dokumente, Autorenhinweise und Nutzungshinweise auf Deutsch und Englisch bereitstellen; GPL-3.0-only für eigene Anteile.
- [x] Relevante öffentliche Shelly-/Victron-Referenzquellen auf längere wortgleiche Codefragmente vergleichen; Quellen und Unterschiede dokumentieren. Dies ist keine juristische Freigabebescheinigung.
- [x] C++-Einzeltests und ESPHome-2026.9.1-Konfigurationsprüfung erfolgreich.
- [x] **Vollständige Firmware in isolierter GitHub Actions-Umgebung erfolgreich kompiliert** (synthetische Testkonfiguration; kein Gerät geflasht).
- [x] Aktuelle GitHub-Dateien manuell prüfen und automatische Datenschutzprüfung für künftige Commits ergänzen.

## Veröffentlichung abgeschlossen / weiterhin zu beachten

- [x] Geprüfte Dateien **ohne alte Alpha-Commits, Branches und Pull Requests** in ein neues Repository mit frischem Verlauf übernommen; das Entwicklungsarchiv bleibt privat.
- [x] Den neuen GitHub-Dateibaum mit dem geprüften Quellbestand abgeglichen; GitHub-Actions-Datenschutztest, C++-Tests und vollständige Firmware-Kompilierung bestanden.
- [x] Repository-Inhaber hat ausschließlich das bereinigte Repository auf **Public** gestellt; das Entwicklungsarchiv bleibt **Private**.

## Als dokumentierte Community-Aufgaben offen (keine Voraussetzung für Quellcodeveröffentlichung)

- [ ] Echte Cerbo-Zertifikate, Kopplung, Hardwareübertragung, Reconnect und längeren Betrieb mit den zwei Änderungen testen.
- [ ] Zertifikatswechsel, NVS-Token-Speicher und vollständige FreeRTOS-/ESPHome-Nebenläufigkeit weiter prüfen.
- [ ] Erweiterung auf mehr als zwei Sensoren entwickeln und praktisch testen.
- [ ] Bei künftiger Übernahme weiterer Fremdcodeanteile Lizenz-/Copyright-/NOTICE-Pflichten neu prüfen.

**Wichtig:** Die Startseite [README.md](../README.md) wurde auf Wunsch des Projektinhabers später auf **Deutsch und Englisch** umgestellt. Die getrennten Sprachfassungen stehen in [README.de.md](../README.de.md) und [README.en.md](../README.en.md). [Sicherer Veröffentlichungsweg](PUBLISHING.de.md).
