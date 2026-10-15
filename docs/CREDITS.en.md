# Sources, contributors and licenses (English)

**Project baseline:** A privately deployed ESPHome/ESP32 integration (stage 4.3.1) observed working with two SolarSense devices. This publication source is a sanitized adaptation of that design, not a verbatim redistribution of third-party firmware. Original contributions here are offered under **GPL-3.0-only**. Existing third-party rights and obligations remain applicable.

- **Thiemo van Engelen** (`ThiemoVanEngelen`): principal contributor of the original [Shelly Victron BLE Bridge](https://github.com/ALLTERCO/shelly-script-examples/blob/main/power-energy/victron-ble-bridge.shelly.js), submitted via [PR #217](https://github.com/ALLTERCO/shelly-script-examples/pull/217). The [Shelly examples repository](https://github.com/ALLTERCO/shelly-script-examples) carries **Apache-2.0**. The ESP32/ESPHome code uses its documented concept and protocol shape; the original JavaScript is not republished here.
- **Shelly / ALLTERCO**: maintainers of the upstream example and subsequent contributions, as documented in upstream history.
- **Victron Energy**: SolarSense BLE field format, GX BLE gateway protocol and official [SolarSense decoder reference](https://github.com/victronenergy/dbus-ble-sensors/blob/master/src/victron-solarsense.c). No blanket root license was verified for that referenced repository; our decoder is not presented as an officially licensed Victron implementation.
- **ESPHome** contributors: ESPHome/ESP-IDF runtime and BLE proxy. [ESPHome 2026.9.1 licensing](https://github.com/esphome/esphome/blob/2026.9.1/LICENSE) (GPLv3 for C++ runtime; some other parts MIT); [Bluetooth Proxies](https://github.com/esphome/bluetooth-proxies) (Apache-2.0).
- **node-red-contrib-victron-ble**: MIT-licensed data-format comparison reference; [repository](https://github.com/node-red-contrib/node-red-contrib-victron-ble). No deliberate code copying.
- **Project contribution:** GitHub `Benny1496`, with AI assistance for drafting documentation and code changes. This statement does not assign copyright to an AI or replace source-provenance review.

**Unofficial community project.** Not affiliated with or endorsed by Victron Energy, Shelly or ESPHome. Original author and license notices must be preserved whenever upstream code is incorporated. No independent legal opinion has been obtained for this source preview.
