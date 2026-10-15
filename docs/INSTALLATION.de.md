# Installation (Deutsch)

## Voraussetzungen

ESP32, ESPHome (Referenz 2026.9.1 mit ESP-IDF), Home Assistant, zwei SolarSense-BLE-Sensoren und ein Cerbo GX mit unterstütztem `/ble-gw/`-Gateway-Endpunkt. Für weitere Sensoren ist diese live-basierte Vorlage noch nicht erweitert oder getestet.

## Vorbereitung

1. Den Ordner `esphome/` in ein **separates Testprojekt** übernehmen. `solarsense-bridge.yaml` und `victron_bridge_43.h` müssen im selben Konfigurationsordner liegen.
2. `secrets.example.yaml` als Vorlage für eine lokale `secrets.yaml` kopieren. Eigene Werte setzen: WLAN, ESPHome-API-Verschlüsselung, Sensor-MACs 1 und 2, Gateway-MAC, einmalige Pairing-Gerätekennung und Cerbo-HTTPS-URL. Die MACs für diese Vorlage im üblichen Format mit **Großbuchstaben** angeben.
3. Öffentliches vertrauenswürdiges CA-/Serverzertifikat des eigenen Cerbo unter dem in `cerbo_ca_path` angegebenen Pfad bereitstellen. Der Hostname der HTTPS-URL muss zum Zertifikat passen. Siehe [Sicherheit](SECURITY.de.md).
4. ESPHome-Konfiguration zuerst validieren und kompilieren. Keine produktive Firmware ungeprüft überschreiben. `!secret`-Werte werden erst aus der lokalen Datei aufgelöst.

## Koppeln und verwenden

1. Im Cerbo GX den dafür vorgesehenen Bluetooth-Gateway-Kopplungsmodus aktivieren.
2. In Home Assistant die Schaltfläche **„Victron Bridge mit Cerbo koppeln“** betätigen. Der Bootstrap `remoteconsole:` mit leerem Passwort ist **kein persönlicher Schlüssel**, funktioniert aber nur im passenden Kopplungskontext. Niemals eigene Administratorpasswörter in Git eintragen.
3. Den Kopplungsstatus prüfen. Gerätetoken werden im ESP32-NVS gespeichert, nicht als Home-Assistant-Entitäten ausgegeben. NVS ist kein verschlüsselter Tresor: physischen Zugriff schützen und bei Gerätewechsel Token widerrufen/neu koppeln.
4. Die beiden BLE-Messwertgruppen in Home Assistant prüfen; erst danach den Schalter **„Victron Bridge Übertragung aktiv“** einschalten. Nach jedem Neustart ist er automatisch **AUS**.
5. Die Übertragungszähler und den Cerbo-Sensorstatus kontrollieren. HTTP 201 bedeutet angenommene Anfrage, nicht zwangsläufig bestätigte D-Bus-Darstellung.

## Hinweise

Die Namen „Südost“ und „Nordwest“ sowie die zugehörigen internen IDs stammen aus dem bewährten Zwei-Sensor-Projekt. Sie sind nur Bezeichnungen, keine echten veröffentlichten Sensoradressen. Bei Bedarf lokal anpassen; die Namen sind für die Funktion nicht erforderlich. Die Installation wurde mit dem neuen Zertifikats-/Duplikat-Verhalten **nicht vollständig auf Hardware geprüft**. Bei TLS-Fehlern keine Zertifikatsprüfung abschalten.
