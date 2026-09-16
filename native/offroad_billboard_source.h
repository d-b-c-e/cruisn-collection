// SPDX-License-Identifier: BSD-3-Clause
// Static source fields only. Caller binds current indexed hit bits/materials to
// the actual scene. Damaged/custom/alternate-binding objects remain unsupported.
#pragma once
#include "offroad_future_sections.h"

namespace cruisn { namespace offroad_billboard_source {
inline bool descriptor(const std::array<uint32_t,11> &definition,uint32_t number,
    uint32_t ordinal,uint32_t count,const std::array<uint32_t,3> &binding,
    uint32_t hit_index,uint32_t hit_bits,bool &supported,std::array<uint32_t,22> &result)
{
    supported=false;result={};
    if(!count || count>256 || ordinal>=count || number>255)return false;
    const auto flags=definition[0];
    if(flags!=0x804 && flags!=0x800804)return true;
    if(flags&0x800000) {
        if(hit_index!=(definition[3]>>16))return false;
        if(hit_bits&(1U<<(hit_index&31)))return true;
    }
    if(!offroad_future::rom_span(definition[1],7) || !offroad_future::rom_span(binding[0],1) ||
        binding[1]>0x7fff || binding[2]>0xffff)return false;
    std::array<uint32_t,22> output{};
    output[5]=flags;output[6]=((count-1-ordinal)<<24)|(number<<16)|0x8000;
    output[7]=definition[3];output[8]=definition[2];
    for(unsigned i=0;i<6;++i)output[11+i]=definition[5+i];
    for(unsigned i=0;i<3;++i)output[17+i]=binding[i];
    output[20]=definition[1];supported=true;result=output;return true;
}
} }
