#include "solarsense_decoder.h"
#include "sensor_registry.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>

using solarsense::DecodeResult;
using solarsense::Reading;

// DE: Kuenstliches, reproduzierbares Testpaket; KEINE privaten Sensordaten.
// EN: Synthetic, deterministic packet; NOT captured from a real user's sensor.
std::array<std::uint8_t, 23> sample() {
  std::array<std::uint8_t, 23> b{};
  b[0] = 0x10; b[4] = 0xFF; b[7] = 0x01; b[12] = 0xFF;
  const std::uint32_t power = 5000;
  const std::uint32_t yield = 1250;
  const std::uint32_t irr = 8500;
  const std::uint32_t temp = 1050;
  b[13] = power & 0xFF; b[14] = (power >> 8) & 0xFF;
  b[15] = ((power >> 16) & 0x0F) | ((yield & 0x0F) << 4);
  b[16] = (yield >> 4) & 0xFF; b[17] = (yield >> 12) & 0xFF;
  b[18] = irr & 0xFF;
  b[19] = ((irr >> 8) & 0x3F) | ((temp & 0x03) << 6);
  b[20] = (temp >> 2) & 0xFF;
  b[21] = (temp >> 10) & 0x01;
  return b;
}

int main() {
  auto data = sample();
  Reading r{};
  assert(solarsense::decode_manufacturer_payload(data.data(), data.size(), r) == DecodeResult::ok);
  assert(r.estimated_available_power_w.valid && r.estimated_available_power_w.amount == 5000);
  assert(r.irradiance_w_m2.valid && r.irradiance_w_m2.amount == 850);
  assert(r.todays_yield_kwh.valid && r.todays_yield_kwh.amount == 12.5);
  assert(r.cell_temperature_c.valid && r.cell_temperature_c.amount == 45);

  assert(solarsense::decode_manufacturer_payload(nullptr, data.size(), r) == DecodeResult::null_buffer);
  assert(solarsense::decode_manufacturer_payload(data.data(), 21, r) == DecodeResult::too_short);
  auto invalid_header = data;
  invalid_header[4] = 0;
  assert(solarsense::decode_manufacturer_payload(invalid_header.data(), invalid_header.size(), r) == DecodeResult::unsupported_record);
  assert(!r.irradiance_w_m2.valid);  // DE: Alte Werte bei Fehler loeschen / EN: Clear stale data on error

  auto absent = data;
  // DE: Platzhalterwerte bedeuten 'keine Daten' und sind keine gueltigen Messwerte.
  // EN: Sentinel values mean missing data and must NOT appear as normal measurements.
  absent[13] = 0xFF; absent[14] = 0xFF; absent[15] = 0xFF;
  absent[16] = 0xFF; absent[17] = 0xFF;
  absent[18] = 0xFF; absent[19] = 0xFF;
  absent[20] = 0xFF; absent[21] = 0xFF;
  assert(solarsense::decode_manufacturer_payload(absent.data(), absent.size(), r) == DecodeResult::ok);
  assert(!r.estimated_available_power_w.valid);
  assert(!r.todays_yield_kwh.valid);
  assert(!r.irradiance_w_m2.valid);
  assert(!r.cell_temperature_c.valid);

  solarsense::SensorRegistry registry;
  assert(registry.add_sensor("02:00:00:00:00:01", "Sample roof A"));
  assert(registry.add_sensor("02:00:00:00:00:02", "Sample roof B"));
  assert(registry.add_sensor("02:00:00:00:00:03", "Sample roof C"));
  assert(!registry.add_sensor("02:00:00:00:00:02", "Duplicate"));
  assert(!registry.add_sensor("INVALID", "Bad MAC"));
  assert(registry.sensors().size() == 3);
  assert(!registry.accept("02:00:00:00:00:01", 0x0000, data.data(), data.size(), data.data(), data.size(), -60, 1000));
  assert(!registry.accept("02:00:00:00:00:04", solarsense::kManufacturerId, data.data(), data.size(), data.data(), data.size(), -60, 1000));
  assert(registry.accept("02:00:00:00:00:03", solarsense::kManufacturerId, data.data(), data.size(), data.data(), data.size(), -70, 2000));
  assert(registry.sensors()[2].valid_packets == 1);
  assert(registry.sensors()[2].latest.estimated_available_power_w.amount == 5000);
  assert(registry.sensors()[2].original_advertisement.size() == data.size());
  assert(registry.sensors()[0].valid_packets == 0);
  std::cout << "OK: decoder, bad input, sentinel values, three-sensor registry\n";
}
