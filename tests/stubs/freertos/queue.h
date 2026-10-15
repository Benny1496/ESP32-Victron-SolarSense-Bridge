#pragma once
#include "FreeRTOS.h"
inline QueueHandle_t xQueueCreate(unsigned int,std::size_t){return reinterpret_cast<QueueHandle_t>(1);}
inline int xQueueSend(QueueHandle_t,const void*,int){return pdTRUE;}
inline int xQueueReceive(QueueHandle_t,void*,int){return 0;}
inline unsigned int uxQueueMessagesWaiting(QueueHandle_t){return 0;}
