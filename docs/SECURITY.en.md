# Security and privacy (English)

- Never commit real Wi-Fi data, API keys, GX tokens, BLE/gateway MACs, LAN IPs, binary firmware or raw diagnostics, even to a private Git branch.
- Site-specific configuration belongs in a private `secrets.yaml`; `secrets.example.yaml` intentionally contains unusable synthetic values.
- `http_request.verify_ssl: true` and a separately obtained **trusted public** CA/server certificate are required. The HTTPS URL must use an identity covered by the certificate; connecting directly to an IP is valid only if the certificate covers that IP. Redirects are disabled.
- Verify the trust anchor outside the untrusted first connection. Do not disable TLS verification or fall back to cleartext HTTP.
- Pairing bootstrap `Basic cmVtb3RlY29uc29sZTo=` decodes to `remoteconsole:` with an empty password for the intended pairing flow. It is **not** a personal GX token. Behavior can depend on GX version.
- As in live firmware 4.3.1, the GX-issued token is saved in ESP32 NVS. NVS is not automatically encrypted at rest. Restrict physical access and revoke tokens for lost/replaced devices.
- Network calls still use a FreeRTOS worker. The 4.3.1 worker had positive real-world tests, but no formal ESPHome threading audit or extended test of the new TLS changes has been completed.
- Do not publish private DNS names, certificate context or raw network logs in GitHub issues.
- Never publish the unmodified original development ZIP.
