#pragma once
#include "FreeRTOS.h"
inline unsigned int xTaskGetTickCount(){return 100;}
inline int xTaskCreatePinnedToCore(void (*)(void*),const char*,int,void*,int,TaskHandle_t* out,int){*out=reinterpret_cast<TaskHandle_t>(1);return pdPASS;}
