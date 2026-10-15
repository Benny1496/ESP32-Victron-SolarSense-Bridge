#pragma once
// ESP32 SolarSense -> Victron GX, based on the live-tested 4.3.1 worker.
// DE: Transport weiterhin in einem FreeRTOS-Task. Kein Zugriff auf HA-Entitaeten im Worker.
// EN: Transport stays in a FreeRTOS task. HA entities are only touched from the main loop.
// Changes: user-provided GX URL/MACs; TLS verified by ESPHome http_request;
// skip byte-identical advertisements until a conservative periodic refresh.
// DE: Veraenderungen: konfigurierbare GX-/Sensoradressen, geprueftes TLS,
// keine erneute Sendung gleicher Advertisements vor dem Refresh.
#include <atomic>
#include <cstring>
#include <string>
#include <vector>
#include "esphome/components/http_request/http_request.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

namespace victron_bridge_43 {
struct Request {
  char auth[340];
  char so_hex[80];
  char nw_hex[80];
  int so_rssi;
  int nw_rssi;
};
struct Result { int status; uint32_t elapsed_ms; };

inline std::string encode64(const std::string &text) {
  const char *abc="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string out;
  out.reserve(((text.size()+2)/3)*4);
  for (size_t i=0;i<text.size();i+=3) {
    uint32_t a=static_cast<uint8_t>(text[i]);
    uint32_t b=i+1<text.size()?static_cast<uint8_t>(text[i+1]):0;
    uint32_t c=i+2<text.size()?static_cast<uint8_t>(text[i+2]):0;
    uint32_t n=(a<<16)|(b<<8)|c;
    out+=abc[(n>>18)&63]; out+=abc[(n>>12)&63];
    out+=i+1<text.size()?abc[(n>>6)&63]:'=';
    out+=i+2<text.size()?abc[n&63]:'=';
  }
  return out;
}

// DE: Nur gueltig formatierte XX:XX:XX:XX:XX:XX-MAC-Adressen zulassen.
// EN: Only accept syntactically valid XX:XX:XX:XX:XX:XX MACs.
inline bool valid_mac(const std::string &mac) {
  if (mac.size() != 17) return false;
  for (size_t i=0;i<17;i++) {
    const char c=mac[i];
    if (i%3==2) { if (c!=':') return false; }
    else if (!((c>='0' && c<='9') || (c>='A' && c<='F') || (c>='a' && c<='f'))) return false;
  }
  return true;
}

// DE: Weiterleitung dokumentiert in docs/TRANSMISSION.de.md.
// EN: Forwarding documented in docs/TRANSMISSION.en.md.
constexpr uint32_t kIdenticalRefreshMs = 15000;
inline bool should_forward(bool have_success, const std::string &last_so,
                           const std::string &last_nw, const Request &req,
                           uint32_t now_ms, uint32_t last_success_ms) {
  if (!have_success) return true;
  if (last_so != req.so_hex || last_nw != req.nw_hex) return true;
  return static_cast<uint32_t>(now_ms-last_success_ms)>=kIdenticalRefreshMs;
}

class Bridge {
 public:
  bool start(esphome::http_request::HttpRequestComponent *http,
             const std::string &url, const std::string &gateway_mac,
             const std::string &so_mac, const std::string &nw_mac) {
    if (task_ != nullptr) return true;
    if (http == nullptr || url.rfind("https://",0)!=0 ||
        url.find("/ble-gw/")==std::string::npos ||
        !valid_mac(gateway_mac) || !valid_mac(so_mac) || !valid_mac(nw_mac)) return false;
    http_=http;
    url_=url; gateway_mac_=gateway_mac; so_mac_=so_mac; nw_mac_=nw_mac;
    requests_=xQueueCreate(1,sizeof(Request));
    results_=xQueueCreate(4,sizeof(Result));
    if (!requests_ || !results_) return false;
    if (xTaskCreatePinnedToCore(task_entry_,"victron43_https",10240,this,1,&task_,1)!=pdPASS) {
      task_=nullptr;
      return false;
    }
    return true;
  }
  bool submit(const std::string &name,const std::string &password,
              const std::string &so,const std::string &nw,int so_rssi,int nw_rssi) {
    if (!requests_ || task_==nullptr || name.empty() || password.empty() ||
        so.size()!=62 || nw.size()!=62) return false;
    if (busy_.load() || uxQueueMessagesWaiting(requests_)!=0) return false;
    Request req{};
    const auto auth="Basic "+encode64(name+":"+password);
    if (auth.size()>=sizeof(req.auth)) return false;
    std::memcpy(req.auth,auth.c_str(),auth.size()+1);
    std::memcpy(req.so_hex,so.c_str(),so.size()+1);
    std::memcpy(req.nw_hex,nw.c_str(),nw.size()+1);
    req.so_rssi=so_rssi;
    req.nw_rssi=nw_rssi;
    const bool queued=xQueueSend(requests_,&req,0)==pdTRUE;
    std::memset(&req,0,sizeof(req));
    return queued;
  }
  bool get_result(Result &result) { return results_ && xQueueReceive(results_,&result,0)==pdTRUE; }
  bool busy() const { return busy_.load() || (requests_ && uxQueueMessagesWaiting(requests_)>0); }
 private:
  static void task_entry_(void *arg) { static_cast<Bridge*>(arg)->run_(); }
  void run_() {
    Request req{};
    for (;;) {
      if (xQueueReceive(requests_,&req,portMAX_DELAY)!=pdTRUE) continue;
      busy_.store(true);
      const uint32_t begun=static_cast<uint32_t>(xTaskGetTickCount()*portTICK_PERIOD_MS);
      // Identical advertisement bytes need only periodic refresh (RSSI alone does not trigger a POST).
      // Identische Nutzdaten nur zyklisch auffrischen; reine RSSI-Aenderungen loesen keinen POST aus.
      if (!should_forward(have_success_,last_success_so_,last_success_nw_,req,begun,last_success_ms_)) {
        std::memset(&req,0,sizeof(req)); busy_.store(false); continue;
      }
      std::string body="{\"data\":{\"gw_mac\":\""+gateway_mac_+"\",\"tags\":{";
      body+="\""+so_mac_+"\":{\"rssi\":"+std::to_string(req.so_rssi)+",\"data\":\""+req.so_hex+"\"},";
      body+="\""+nw_mac_+"\":{\"rssi\":"+std::to_string(req.nw_rssi)+",\"data\":\""+req.nw_hex+"\"}}}}";
      std::vector<esphome::http_request::Header> headers={
        {"Content-Type","application/json"},{"Authorization",std::string(req.auth)}};
      int status=-1;
      if (http_ != nullptr) {
        auto response=http_->post(url_,body,headers);
        if (response) { status=response->status_code; response->end(); }
      }
      if (status>=200 && status<300) {
        last_success_so_=req.so_hex;last_success_nw_=req.nw_hex;
        last_success_ms_=static_cast<uint32_t>(xTaskGetTickCount()*portTICK_PERIOD_MS);
        have_success_=true;
      }
      Result result{status,static_cast<uint32_t>(xTaskGetTickCount()*portTICK_PERIOD_MS)-begun};
      xQueueSend(results_,&result,0);
      std::memset(&req,0,sizeof(req));
      busy_.store(false);
    }
  }
  esphome::http_request::HttpRequestComponent *http_{nullptr};
  std::string url_,gateway_mac_,so_mac_,nw_mac_;
  std::string last_success_so_,last_success_nw_;
  bool have_success_{false};
  uint32_t last_success_ms_{0};
  QueueHandle_t requests_{nullptr};
  QueueHandle_t results_{nullptr};
  TaskHandle_t task_{nullptr};
  std::atomic<bool> busy_{false};
};
inline Bridge bridge;
}  // namespace victron_bridge_43
