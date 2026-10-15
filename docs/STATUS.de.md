# Entwicklungs- und Teststand (Deutsch)

Stand: 15. Oktober 2026. Ausgangspunkt ist die **produktive Stufe 4.3.1**.

**Im ursprünglichen Live-System beobachtet:** Zwei Victron SolarSense BLE-Sensoren liefern Messwerte an Home Assistant; ihre Original-Advertisements werden durch einen FreeRTOS-Task über den Cerbo-GX-Endpunkt `/ble-gw/` übertragen. Der dokumentierte Nachttest erfasste über 10.400 erfolgreich beantwortete HTTP-201-Übertragungen und einen selbstständig überwundenen Kommunikationsfehler. HTTP 201 belegt nicht automatisch eine dauerhaft sichtbare GX-D-Bus-Anzeige.

**Neue Veröffentlichungsfassung:** Echte MACs, LAN-Adressen und der ESPHome-API-Schlüssel sind ausgelagert (`!secret`). HTTPS mit Zertifikats- und Hostnamenprüfung und deaktivierten Redirects ist vorbereitet. Identische BLE-Nutzdaten werden bis zum 15-Sekunden-Refresh nicht erneut gesendet.

**Erfolgreich geprüft:** C++-Einzeltests; ESPHome-2026.9.1-Konfigurationsprüfung und **vollständige isolierte Firmware-Kompilierung in GitHub Actions** mit ausschließlich künstlichen Zugangsdaten und Testzertifikat. Ein automatischer Datenschutzfilter für bekannte private IPs, nicht freigegebene MACs und private Schlüssel ergänzt die manuelle Dateiprüfung.

**Nicht als getestet behaupten:** Die neue TLS-/Duplikat-Kombination wurde nicht am produktiven ESP32 mit echtem Cerbo GX geprüft. Offen sind Praxistests von Zertifikatswechsel, Pairing, Fehler-/Wiederholungsfällen, längerem Betrieb sowie die Reichweite von mehr als zwei Sensoren. Die Vorlage konfiguriert tatsächlich **zwei** Sensoren; mehr sind als Community-Weiterentwicklung willkommen.

**Veröffentlichung:** Das aktuelle Repository ist **öffentlich** und wurde mit einem neuen Git-Verlauf angelegt. Der frühere Alpha-Branch und der alte Pull Request befinden sich ausschließlich im **privaten Entwicklungsarchiv**, nicht in diesem Repository. Die Startseite und die Projektdokumentation sind in **Deutsch und Englisch** verfügbar. Hintergrund: [PUBLISHING.de.md](PUBLISHING.de.md).

**Community-Quellcode-Vorschau, keine produktiv zertifizierte Firmware und keine juristische Gewährleistung.**
