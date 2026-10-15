#pragma once

// Prototype: configurable count of sensors, no hardcoded roof sides.
// This class is NOT thread-safe; update it only from one ESPHome/main-loop context.
// Transport to GX and Home Assistant discovery are not implemented here.

#include "solarsense_decoder.h"
#include <cctype>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace solarsense {

struct TrackedSensor {
  std::string mac;
  std::string label;
  Reading latest{};
  std::vector<std::uint8_t> original_advertisement;
  int rssi{0};
  std::uint32_t last_seen_ms{0};
  std::uint32_t valid_packets{0};
  bool received{false};
};

class SensorRegistry {
 public:
  bool add_sensor(std::string mac, std::string label) {
    if (!normalize_mac(mac) || label.empty() || find(mac) != nullptr) return false;
    TrackedSensor sensor{};
    sensor.mac = std::move(mac);
    sensor.label = std::move(label);
    sensors_.push_back(std::move(sensor));
    return true;
  }

  // Manufacturer ID and sensor MAC are checked before a record is stored.
  // Full original advertising bytes are preserved for later GX forwarding.
  bool accept(const std::string& address, std::uint16_t manufacturer_id,
              const std::uint8_t* manufacturer_bytes, std::size_t manufacturer_length,
              const std::uint8_t* advertisement, std::size_t advertisement_length,
              int rssi, std::uint32_t now_ms) {
    if (manufacturer_id != kManufacturerId || advertisement == nullptr ||
        advertisement_length == 0 || advertisement_length > 62) return false;
    std::string mac = address;
    if (!normalize_mac(mac)) return false;
    TrackedSensor* sensor = find(mac);
    if (sensor == nullptr) return false;
    Reading reading;
    if (decode_manufacturer_payload(manufacturer_bytes, manufacturer_length, reading) != DecodeResult::ok) {
      return false;
    }
    sensor->original_advertisement.assign(advertisement, advertisement + advertisement_length);
    sensor->latest = reading;
    sensor->rssi = rssi;
    sensor->last_seen_ms = now_ms;
    ++sensor->valid_packets;
    sensor->received = true;
    return true;
  }

  const std::vector<TrackedSensor>& sensors() const { return sensors_; }

 private:
  static bool normalize_mac(std::string& mac) {
    if (mac.size() != 17) return false;
    for (std::size_t i = 0; i < mac.size(); ++i) {
      if (i % 3 == 2) {
        if (mac[i] != ':') return false;
      } else {
        if (!std::isxdigit(static_cast<unsigned char>(mac[i]))) return false;
        mac[i] = static_cast<char>(std::toupper(static_cast<unsigned char>(mac[i])));
      }
    }
    return true;
  }
  TrackedSensor* find(const std::string& normalized_mac) {
    for (auto& sensor : sensors_) if (sensor.mac == normalized_mac) return &sensor;
    return nullptr;
  }
  std::vector<TrackedSensor> sensors_;
};

}  // namespace solarsense
