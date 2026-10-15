# Release checklist (English)

## Completed in current source

- [x] Use deployed stage 4.3.1 as the code basis and preserve Home Assistant/BLE behavior; no changes to the live device.
- [x] Remove genuine device addresses and private API keys from publication examples.
- [x] Require verified HTTPS certificates and disable redirects.
- [x] Keep the background worker; avoid unnecessary repeated posts of identical BLE data until periodic refresh.
- [x] Provide paired German/English documentation, author/source notices and GPL-3.0-only licensing for original contributions.
- [x] Compare relevant public Shelly/Victron reference sources for substantial verbatim matching and document origin and differences; this is not a legal opinion.
- [x] Pass isolated C++ unit tests and ESPHome 2026.9.1 configuration validation.
- [x] **Successfully compile complete firmware in isolated GitHub Actions** (synthetic test configuration; no hardware flashed).
- [x] Manually inspect current tracked files and add automated privacy checks for future commits.

## Publication completed / continuing precautions

- [x] Transferred audited files to a **new repository with clean history**, without old Alpha commits, branches or PRs. Original development repo remains private.
- [x] Compared all public files to the audited source; the new repository passed GitHub Actions privacy, C++ and complete firmware build checks.
- [x] Repository owner set **only this clean repository** to **Public**; private archive stays private.

## Transparent community follow-ups (not blockers for source publication)

- [ ] Verify real Cerbo TLS cert, pairing, data forwarding, retries and long-running behavior with the two new changes.
- [ ] Further review certificate renewal, NVS token storage and ESPHome/FreeRTOS concurrency.
- [ ] Implement and test additional sensors beyond the two in the current configuration.
- [ ] Review source provenance and required copyright/license/NOTICE materials whenever additional third-party code is copied.

**Note:** The repository owner later requested a **German-English** homepage; [README.md](../README.md) now introduces both languages. Separate versions: [README.de.md](../README.de.md) and [README.en.md](../README.en.md). [Clean publication process](PUBLISHING.en.md).
