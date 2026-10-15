// EN: Standalone checks for forwarding unchanged BLE bytes.
// DE: Eigenstaendige Tests zur Vermeidung doppelter BLE-Weiterleitung.
#include "../esphome/victron_bridge_43.h"
#include <cassert>
#include <cstring>
#include <iostream>
int main() {
 using namespace victron_bridge_43;
 Request r{};
 std::strcpy(r.so_hex,"0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCD");
 std::strcpy(r.nw_hex,"FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA987654");
 assert(should_forward(false,"","",r,100,0));
 assert(!should_forward(true,r.so_hex,r.nw_hex,r,5000,0));
 assert(should_forward(true,r.so_hex,r.nw_hex,r,15000,0));
 assert(should_forward(true,r.so_hex,r.nw_hex,r,20,UINT32_MAX-15000));
 assert(!should_forward(true,r.so_hex,r.nw_hex,r,20,UINT32_MAX-1000));
 assert(should_forward(true,"different",r.nw_hex,r,100,50));
 assert(valid_mac("02:00:00:00:00:01"));
 assert(!valid_mac("NOT_A_MAC"));
 assert(encode64("remoteconsole:")=="cmVtb3RlY29uc29sZTo=");
 std::cout<<"PASS: duplicate/refresh/wraparound, MAC and pairing-bootstrap checks\\n";
}
