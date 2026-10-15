# Sicherheit und Privatsphäre (Deutsch)

- Keine echten WLAN-Daten, API-Schlüssel, GX-Tokens, BLE-MACs, Gateway-MACs, lokalen IPs, Firmware-Binärdateien oder Diagnose-Logs einchecken – auch nicht in private Git-Commits.
- Alle standortbezogenen Werte kommen aus einer privaten `secrets.yaml`. Das mitgelieferte `secrets.example.yaml` enthält ausschließlich offensichtlich künstliche Beispiele. Es ist **keine** einsatzbereite Konfiguration.
- `http_request.verify_ssl: true` und ein selbst beschafftes, vertrauenswürdiges CA-/Serverzertifikat sind erforderlich. Die HTTPS-URL muss einen zum Zertifikat passenden Hostnamen tragen; ein reiner IP-Aufruf funktioniert nur, wenn das Zertifikat genau diese IP als Identität abdeckt. Weiterleitungen sind deaktiviert.
- Den Zertifikats-Fingerabdruck/Vertrauensanker außerhalb einer ungesicherten Erstverbindung prüfen. Kein `verify_ssl: false` und keine improvisierten HTTP-Fallbacks.
- Der Pairing-Bootstrap `Basic cmVtb3RlY29uc29sZTo=` entspricht `remoteconsole:` mit leerem Passwort **im vorgesehenen Kopplungsmodus**. Es ist kein individueller Token. Das Verhalten des Cerbo kann versionsabhängig sein.
- Das vom GX ausgegebene Token wird wie in der Live-Version 4.3.1 in NVS gespeichert. NVS ist standardmäßig kein verschlüsselter Tresor. Physische Gerätezugriffe einschränken und Token widerrufen, wenn das Gerät verloren geht.
- Die HTTPS-Übertragung findet weiter in einem FreeRTOS-Worker statt. Das hatte in 4.3.1 gute Praxisergebnisse, aber eine formale ESPHome-Thread-Sicherheitsprüfung und ein Langzeitversuch mit den Sicherheitsänderungen fehlen noch.
- Private DNS-Namen oder Zertifikatsinhalte aus dem eigenen Netz nicht für öffentliche Fehlermeldungen hochladen.
- Niemals das komplette ursprüngliche Arbeits-ZIP als öffentlichen Quellcode verwenden.
