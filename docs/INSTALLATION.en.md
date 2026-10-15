# Installation (English)

## Requirements

An ESP32, ESPHome (reference 2026.9.1 with ESP-IDF), Home Assistant, two SolarSense BLE sensors and a Cerbo GX supporting the `/ble-gw/` gateway interface. This live-system-based template has not yet been extended or tested for more sensors.

## Prepare

1. Copy `esphome/` into a **separate ESPHome test project**. Keep `solarsense-bridge.yaml` alongside `victron_bridge_43.h`.
2. Copy `secrets.example.yaml` to a private `secrets.yaml` and fill in Wi-Fi, ESPHome API encryption key, both sensor MACs, the gateway MAC, a unique pairing device ID and the Cerbo HTTPS URL. Use **uppercase** hex letters in MAC addresses for this template.
3. Supply an authentic, trusted **public** Cerbo CA/server certificate at the path configured as `cerbo_ca_path`. The HTTPS hostname must match the certificate. See [Security](SECURITY.en.md).
4. Validate and compile the ESPHome configuration before attempting any installation. Never replace a working ESP32 firmware without an independent test. Local `!secret` entries are resolved at build time.

## Pairing and forwarding

1. Put the GX into its supported Bluetooth gateway pairing mode.
2. Press **“Victron Bridge mit Cerbo koppeln”** in Home Assistant. The `remoteconsole:` empty-password bootstrap is not a personal token and is limited to the proper pairing workflow; never place administrator credentials in Git.
3. Verify pairing status. Issued tokens remain in ESP32 NVS, not in Home Assistant entities. NVS is not an encrypted secrets vault: protect physical device access and revoke/re-pair as appropriate.
4. Verify the two BLE sensor groups in Home Assistant. Only then enable **“Victron Bridge Übertragung aktiv”**. Forwarding defaults **OFF** after each restart.
5. Check transmission counters and the GX sensor view. HTTP 201 confirms request acceptance, not necessarily a lasting D-Bus/UI update.

## Notes

The original internal IDs and Home Assistant entity labels use the German names “Südost” and “Nordwest” for sensor one and sensor two. They are labels, **not published real sensor addresses**. Users may customize them locally. The certificate-verification and de-duplication modifications have **not yet passed full on-device integration testing**. Never bypass failed TLS checks.
