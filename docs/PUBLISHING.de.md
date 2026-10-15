# Veröffentlichung und Datenschutz (Deutsch)

## Was geprüft wurde

Der aktuelle Quellcode auf `main` wurde auf echte lokale IP-Adressen, Hardware-MACs, private Schlüssel und bekannte produktive Konfigurationswerte geprüft. ESPHome-Konfiguration und isolierte C++-Tests werden außerdem über GitHub Actions überprüft. `scripts/check_publication_privacy.py` kontrolliert neue Commits auf typische versehentliche Freigaben. **Dieser Filter ist keine Garantie**, weil er unbekannte Geheimnisformate nicht erkennen muss.

Die Original-Firmware Stufe 4.3.1 wird **nicht unverändert veröffentlicht**. Der veröffentlichbare `esphome/`-Ordner nutzt private `secrets.yaml`-Dateien und ein vom Anwender selbst bereitgestelltes TLS-Vertrauenszertifikat. Die bestehenden zwei SolarSense-Sensoren sind die dokumentierte Referenz; HTTPS-Zertifikatsprüfung und 15-Sekunden-Duplikat-Refresh sind neue, noch nicht gemeinsam an der Produktivanlage getestete Änderungen.

## Warum keine einfache Änderung auf Public?

Der bestehende private GitHub-Verlauf enthält den alten Alpha-Branch und einen geschlossenen Pull Request, deren ältere Revisionen projekt- und gerätespezifische Testkontexte erwähnen. Auch gelöschte Dateien oder Branches können in PR-Referenzen beziehungsweise alten Commits weiterhin auffindbar sein. Daher das bestehende private Repository **nicht direkt öffentlich schalten**.

## Sauberer Veröffentlichungsweg

1. Das aktuelle `main` als **Quellcode-Dateien ohne .git-Verzeichnis und ohne Historie** exportieren (beispielsweise `Download ZIP` und entpacken). Nicht den Original-ZIP-Stand 4.3.1 exportieren.
2. Ein **neues, leeres GitHub-Repository** unter dem gewünschten öffentlichen Namen erstellen. **Nicht forken, keinen Import mit Commit-Historie durchführen und keine alten Alpha-Branches übernehmen**. Das Alt-Repository bleibt privat archiviert.
3. Ausschließlich die geprüften Dateien in einem frischen ersten Commit übertragen. `README.md` bewusst unverändert übernehmen, `README.de.md` ergänzt den deutschen Einstieg.
4. Datenschutztest und GitHub-Actions-CI im neuen Repository prüfen. Den Versionsstand ehrlich als Community-Quellcode-Vorschau mit noch ausstehenden Hardwaretests bezeichnen.
5. Der Repository-Inhaber entscheidet anschließend selbst ausdrücklich über `Public`. Keine eigenen Zugangsdaten, lokalen Zertifikate oder Firmware-Dumps veröffentlichen.

**Hinweis:** Ein neuer Git-Verlauf ersetzt keine Überprüfung der tatsächlich übertragenen Dateien. Die allgemeinen Quellen- und Lizenzhinweise stehen unter [CREDITS.de.md](CREDITS.de.md) und [LICENSE.de.md](LICENSE.de.md). Die isolierte Kompilation ist keine Bestätigung der Funktion am realen Cerbo GX.
