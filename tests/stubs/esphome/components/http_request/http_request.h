#pragma once
#include <memory>
#include <string>
#include <vector>
namespace esphome::http_request {
struct Header { std::string name;std::string value; };
class HttpContainer { public: int status_code{201}; void end() {} ;};
class HttpRequestComponent {public: std::shared_ptr<HttpContainer> post(const std::string &,const std::string &,const std::vector<Header> &) { return std::make_shared<HttpContainer>(); }};
}
