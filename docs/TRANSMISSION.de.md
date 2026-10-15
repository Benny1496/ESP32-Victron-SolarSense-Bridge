# BLE-Übertragung und Doppelpakete (Deutsch)

Ausgangspunkt ist der FreeRTOS-Hintergrund-Worker der produktiv beobachteten 4.3.1. Zwei 31-Byte-BLE-Werbepakete werden anhand ihrer konfigurierten Adressen erfasst. Der ESP32 aktualisiert Home Assistant wie bisher; nur die Weiterleitung zum Cerbo erhält eine neue Wiederholungssperre.

**Regel:** Ein gültiger, aktualisierter Datenstand wird beim 3-Sekunden-Takt übermittelt. Waren die zuletzt vom Cerbo mit HTTP 2xx angenommenen Hex-Advertisements beider Sensoren unverändert, entfällt die erneute HTTPS-Anfrage bis zum periodischen Refresh nach **15 Sekunden**. RSSI-Änderungen allein lösen keine vorzeitige Sendung aus, werden aber mit dem nächsten Refresh übernommen. Nach fehlgeschlagenem HTTP-Request ist ein erneuter Versuch ohne Wartezeit auf die nächste Refresh-Grenze möglich.

Der Worker verarbeitet höchstens einen Request gleichzeitig; es werden keine alten Anfragen unbegrenzt angestaut. Sind Tokens oder frische Sensorpakete nicht verfügbar, wird nicht gesendet. Nach einem Neustart bleibt der Schalter AUS. Die beiden Original-Advertisements werden nicht verändert oder zu neu berechneten HA-Werten umgebaut.

**Wichtig:** Das neue 15-Sekunden-Refresh und TLS wurden **noch nicht im gemeinsamen Dauerbetrieb am Cerbo getestet**. Manche Firmwarestände könnten kürzere Aktualisierungsabstände erwarten; bei Problemen Refresh/Empfängerzustand messen, bevor Parameter geändert werden. HTTP 201 beweist nur die HTTP-Annahme.
