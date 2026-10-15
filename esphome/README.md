# ESPHome source / ESPHome-Quellcode

**[Deutsch](#deutsch) · [English](#english)** · [Project start / Projektstart](../README.md)

<a id="deutsch"></a>
## 🇩🇪 Deutsch

Die Datei [`solarsense-bridge.yaml`](solarsense-bridge.yaml) ist die eigentliche ESPHome-Vorlage, [`victron_bridge_43.h`](victron_bridge_43.h) enthält die Hintergrund-HTTPS-Weiterleitung. [`secrets.example.yaml`](secrets.example.yaml) enthält nur künstliche Beispielwerte. Eine **eigene private** `secrets.yaml` und ein verifiziertes Cerbo-Zertifikat müssen lokal bereitgestellt werden.

Die vorhandenen deutschen Home-Assistant-Namen und internen Kennungen wurden absichtlich beibehalten, damit sich das Verhalten der bewährten Zwei-Sensor-Vorlage nicht wegen einer Übersetzung ändert. Englische Bedeutungen und Anpassungshinweise: [Home-Assistant-Anzeigen (DE)](../docs/HOME_ASSISTANT.de.md).

**Sicherheit:** Nicht `verify_ssl: false` setzen, keine echten privaten Zugangsdaten ins Git-Repository übernehmen. [Installation](../docs/INSTALLATION.de.md) · [Sicherheit](../docs/SECURITY.de.md).

<a id="english"></a>
## 🇬🇧 English

[`solarsense-bridge.yaml`](solarsense-bridge.yaml) is the actual ESPHome configuration, and [`victron_bridge_43.h`](victron_bridge_43.h) implements background HTTPS forwarding. [`secrets.example.yaml`](secrets.example.yaml) uses synthetic example data only. Provide your **own private** `secrets.yaml` and independently verified Cerbo trust certificate locally.

Existing German Home Assistant entity labels and internal identifiers are intentionally preserved to avoid breaking the working two-sensor configuration just for localization. English translations and customization notes: [Home Assistant labels (EN)](../docs/HOME_ASSISTANT.en.md).

**Security:** Do not disable `verify_ssl` or commit private credentials. [Installation](../docs/INSTALLATION.en.md) · [Security](../docs/SECURITY.en.md).
