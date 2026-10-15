#pragma once

// DE: Eigenstaendige Implementierung der oeffentlich beschriebenen SolarSense-BLE-Felder.
// DE: Eingabe ist die Victron-Herstellerdaten-Nutzlast, NICHT das komplette BLE-Paket.
// EN: Independent implementation of publicly documented SolarSense BLE data fields.
// EN: Input is the manufacturer-data payload, NOT the complete BLE advertisement.
// DE/EN: Kein Victron-Quellcode kopiert / no Victron source copied.
// Quellen / Sources: https://github.com/victronenergy/dbus-ble-sensors
// Dokumentation / Documentation: docs/SOURCES.de.md and docs/SOURCES.md.

#include <cstddef>
#include <cstdint>

namespace solarsense {

constexpr std::uint16_t kManufacturerId = 0x02E1;

struct Value {
  float amount{0.0f};
  bool valid{false};
};

struct Reading {
  Value estimated_available_power_w;
  Value irradiance_w_m2;
  Value todays_yield_kwh;
  Value cell_temperature_c;
};

enum class DecodeResult {
  ok,
  null_buffer,
  too_short,
  unsupported_record,
};

inline DecodeResult decode_manufacturer_payload(const std::uint8_t* bytes,
                                                 std::size_t length,
                                                 Reading& output) {
  output = {};
  if (bytes == nullptr) return DecodeResult::null_buffer;
  if (length < 22) return DecodeResult::too_short;

  // DE: SolarSense-750-Klartextdatensatz fuer Momentanwerte (0xFF01).
  // EN: SolarSense 750 plaintext instant-readout record (0xFF01).
  if (bytes[0] != 0x10 || bytes[4] != 0xFF || bytes[7] != 0x01) {
    return DecodeResult::unsupported_record;
  }

  const std::uint32_t power = static_cast<std::uint32_t>(bytes[13]) |
                              (static_cast<std::uint32_t>(bytes[14]) << 8) |
                              ((static_cast<std::uint32_t>(bytes[15]) & 0x0FU) << 16);
  const std::uint32_t yield = (static_cast<std::uint32_t>(bytes[15]) >> 4) |
                              (static_cast<std::uint32_t>(bytes[16]) << 4) |
                              (static_cast<std::uint32_t>(bytes[17]) << 12);
  const std::uint16_t irradiance = static_cast<std::uint16_t>(
      static_cast<std::uint16_t>(bytes[18]) |
      ((static_cast<std::uint16_t>(bytes[19]) & 0x3FU) << 8));
  const std::uint16_t temperature = static_cast<std::uint16_t>(
      (static_cast<std::uint16_t>(bytes[19]) >> 6) |
      (static_cast<std::uint16_t>(bytes[20]) << 2) |
      ((static_cast<std::uint16_t>(bytes[21]) & 0x01U) << 10));

  if (power != 0xFFFFFU) output.estimated_available_power_w = {static_cast<float>(power), true};
  if (yield != 0xFFFFFU) output.todays_yield_kwh = {static_cast<float>(yield) / 100.0f, true};
  if (irradiance != 0x3FFFU) output.irradiance_w_m2 = {static_cast<float>(irradiance) / 10.0f, true};
  if (temperature != 0x7FFU) {
    output.cell_temperature_c = {static_cast<float>(temperature) / 10.0f - 60.0f, true};
  }
  return DecodeResult::ok;
}

}  // namespace solarsense
