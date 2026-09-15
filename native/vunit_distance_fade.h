// SPDX-License-Identifier: BSD-3-Clause
// Host-only depth/road metadata contract; original quad bytes stay unchanged.
#pragma once
#include "vunit_far_coverage.h"

namespace cruisn { namespace vunit_fade {
// Retain the entire existing quad/coverage prefix; never encode ownership in UVs.
struct Packet {
    vunit_far::Packet quad;
    uint32_t policy=0; // bit0: authored road, preserve full opacity
};
static_assert(sizeof(Packet)==64 && offsetof(Packet,policy)==60,"distance-fade wire layout");

// Unlike the crossing-only codec, this also permits wholly inside host quads.
// A completely outside quad is not eligible; the producer must omit it.
inline bool decode(const Packet &packet,std::array<float,4> &depths,bool &crossing)
{
    depths={};crossing=false;
    const auto &q=packet.quad;
    if(!q.frame || (q.pad!=3 && q.pad!=7) || packet.policy>1 || q.coverage.far_limit!=240000)return false;
    if(q.pad==7 && packet.policy!=1)return false; // margin coverage is an authored-road permission
    std::array<float,4> values{};unsigned inside=0;
    for(unsigned i=0;i<4;++i)
    {
        const uint32_t w=q.coverage.words[i];const int e=int8_t(w>>24);
        if((w&0x800000) || e<9 || e>18)return false;
        values[i]=std::ldexp(float((w&0x7fffff)|0x800000),e-23);
        if(values[i]<1000 || values[i]>=480000)return false;
        inside+=values[i]<q.coverage.far_limit;
    }
    if(!inside)return false;
    depths=values;crossing=inside!=4;return true;
}
} }
