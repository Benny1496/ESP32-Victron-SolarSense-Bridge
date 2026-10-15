#pragma once
#include <cstddef>
#include <cstdint>
using QueueHandle_t=void*; using TaskHandle_t=void*;
constexpr int pdTRUE=1; constexpr int pdPASS=1;
constexpr uint32_t portTICK_PERIOD_MS=1; constexpr int portMAX_DELAY=10000000;
