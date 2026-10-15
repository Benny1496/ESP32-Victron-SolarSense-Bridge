#pragma once

// Independent implementation of the publicly documented SolarSense BLE fields.
// Input is the Victron manufacturer-data PAYLOAD, not the full BLE advertisement.
// Reference: https://github.com/victronenergy/dbus-ble-sensors
// No Victron source code is copied here. See docs/SOURCES.md.

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

  // SolarSense 750 plaintext instant-readout record (0xFF01).
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
