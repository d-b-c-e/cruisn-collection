// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstdint>
#include <cstring>
namespace cruisn {
struct VunitBootstrapProfile { uint32_t pc, address; };
inline VunitBootstrapProfile vunit_bootstrap_profile(const char *rom)
{
    if(!rom)return {0,0};
    if(!std::strcmp(rom,"crusnusa"))return {0x81,0x40};
    if(!std::strcmp(rom,"crusnwld24"))return {0x6a,0x61ee};
    if(!std::strcmp(rom,"crusnwld"))return {0x6a,0x658f};
    if(!std::strcmp(rom,"offroadc"))return {0x1bf9,0x111f4};
    return {0,0};
}
}
