# Publication and privacy (English)

[Deutsch](PUBLISHING.de.md) · [English](PUBLISHING.en.md) · [Home](../README.md)

## Current public repository

[ESP32-Victron-SolarSense-Bridge](https://github.com/Benny1496/ESP32-Victron-SolarSense-Bridge) is now **public**. It contains the reviewed project source with a **fresh Git history**. The earlier private development repository, abandoned Alpha branch and closed PR remain in a **separate private archive**.

Public files use each user's own private `secrets.yaml` and independently obtained trusted TLS certificate. **No original site's credentials, device addresses, or private certificates** are included.

## What has been checked

- Source files were inspected for known internal network addresses, genuine hardware MACs and private keys. The automatic [privacy guard](../scripts/check_publication_privacy.py) supplements manual review but **cannot guarantee** that every possible secret format will be recognized.
- The fresh public Git history contains **no old Alpha commits or pull requests**.
- C++ unit tests, ESPHome 2026.9.1 configuration validation and **complete firmware compilation** passed using synthetic CI values.
- The published template is not identical to the private live-tested stage 4.3.1: certificate-verified TLS and 15-second duplicate refresh are new and have **not yet been jointly hardware-tested**.

## For future contributions

1. German **or** English contributions are welcome. Please update **both language versions** whenever user-facing behavior changes.
2. Never commit local `secrets.yaml`, private keys, tokens, MAC addresses, internal IPs or raw logs.
3. Run automatic checks before a pull request; distinguish real hardware testing from untested assumptions.
4. A GitHub Actions source-only export contains currently tracked source files, not the old private repository's history.
5. Review author rights and license notices for all reused third-party code: [Credits](CREDITS.en.md).

This page documents a **completed public launch**. It is not an instruction to publish the private archive.
