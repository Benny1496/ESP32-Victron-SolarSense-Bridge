# ESP32 Victron SolarSense Bridge

A work-in-progress ESPHome / ESP32 bridge concept for Victron SolarSense BLE sensors, Home Assistant, and Victron Cerbo GX (Venus OS).

**Status: development prototype; not ready to install or publish as a working bridge.** The production integration is still under review for TLS authentication, source provenance, resource limits, and ESPHome compatibility.

## Design goals

- Support a **configurable number of SolarSense sensors**, not a hard-coded pair. One, two, or more devices should follow the same logic. The maximum reliable number depends on ESP32 memory, BLE reception, network performance, and GX capabilities and must be tested.
- Forward the **original BLE advertisement** to the GX without calibrating or altering measurement payloads.
- Decode the standard SolarSense manufacturer data locally for Home Assistant: irradiance, estimated available PV power, today's yield, and cell temperature.
- Provide received-signal strength and diagnostics for each configured sensor.
- Keep user-specific system configurations and credentials out of source control.

## Included in this draft

- `src/solarsense_decoder.h`: independent C++17 SolarSense manufacturer-payload decoder with invalid-field handling.
- `src/sensor_registry.h`: prototype runtime registry using a variable-sized list of configured sensors, with unaltered advertisement bytes preserved.
- `tests/test_solarsense.cpp`: offline tests using synthetic packets; compiles with `g++`.
- `examples/sensors.example.yaml`: **illustrative configuration only**, not directly usable in ESPHome.
- `docs/SOURCES.md`: source and attribution investigation.
- `docs/RELEASE_CHECKLIST.md`: outstanding work before any publication.

Test locally with:

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -Isrc \
  tests/test_solarsense.cpp -o /tmp/test_solarsense
/tmp/test_solarsense
```

**Not yet implemented in this draft:** ESPHome entity-generation for N sensors, generic GX JSON/HTTPS task, secure pairing, integration build and reliable 3+ sensor hardware tests. The existing production firmware is not changed by this prototype.

Read [docs/SOURCES.md](docs/SOURCES.md) before redistributing. The final license for this new project's combined components has not been settled.
