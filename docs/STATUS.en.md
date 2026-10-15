# Development and test status (English)

As of 15 October 2026, based on the **privately deployed stage 4.3.1** firmware.

**Observed on the original live installation:** Two Victron SolarSense BLE sensors report to Home Assistant while a FreeRTOS task forwards their original advertisements to Cerbo GX `/ble-gw/`. The documented overnight sample recorded over 10,400 successful HTTP-201 responses and one self-recovering transport error. An HTTP 201 alone does not prove persistent GX D-Bus/UI visibility.

**New publication source:** Real device MACs, LAN addresses and ESPHome API key are configured outside Git (`!secret`). HTTPS certificate/hostname verification and disabled redirects are prepared. Byte-identical advertisements are suppressed until a 15-second periodic refresh.

**Successfully checked:** C++ unit tests; ESPHome 2026.9.1 configuration validation and a **complete isolated firmware compilation in GitHub Actions**, using only synthetic credentials and a temporary test certificate. Automated checks for known private LAN IPs, non-example MACs and private keys complement manual file review.

**Not yet claimed as hardware-tested:** The new TLS/duplicate combination has not been exercised on the production ESP32 with an actual Cerbo GX. Certificate rotation, pairing, retry/error cases, sustained operation and capacities beyond two sensors remain to be checked in practical use. The actual template explicitly configures **two** sensors; additional sensors are welcome as future contributions.

**Publication:** This repository is now **public** and was initialized with a **fresh Git history**. The old Alpha branch and closed pull request belong solely to the separate **private development archive**, not to this public repository. The homepage and project documentation are provided in **German and English**. See [PUBLISHING.en.md](PUBLISHING.en.md).

**Community source preview, not a production-certified firmware or legal warranty.**
