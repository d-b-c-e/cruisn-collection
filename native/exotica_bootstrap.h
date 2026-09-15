// SPDX-License-Identifier: BSD-3-Clause
// Verify a complete guest pool rebuild before starting lifetime observation.
#pragma once
#include <cstddef>
#include <cstdint>
#include <utility>

namespace cruisn { namespace exotica_bootstrap {
inline const std::pair<uint32_t,uint32_t> *signatures(size_t &count) {
    static const std::pair<uint32_t,uint32_t> values[]={
        {0xbbf6,0x152010a8},{0xbbf9,0x152010a9},{0xbc64,0x152a10a8},{0xbc67,0x152010a9},
        {0xbbc7,0x086004b0},{0xbbc8,0x152010a9},{0xbbcc,0x1549c000},{0xbbce,0x0269001f},
        {0xbbd4,0x1540c000},{0xbbcb,0x087b04af},{0xbbcf,0x6400bbd2},{0xbbd0,0x1549c000},
        {0xbbd1,0x08080009},{0xbbd2,0x0269001f},{0xb859,0x082267c4},{0xb8cb,0x0840041d},
        {0x696f,0x152d046e},{0x6963,0x0820b47d}};
    count=sizeof(values)/sizeof(values[0]);return values;
}
template<class Read> bool code_matches(Read read) {
    size_t count=0;const auto *code=signatures(count);
    for(size_t i=0;i<count;++i)if(read(code[i].first)!=code[i].second)return false;
    return true;
}
inline bool pool(uint32_t base) {
    return base>=0x1000 && uint64_t(base)+1201*31<=0x40000 &&
        (uint64_t(base)+1201*31<=0x30000 || base>=0x32000);
}
template<class Read>
bool begin(Read read,uint32_t value,uint32_t mask,uint32_t pc,uint32_t &base) {
    if(pc!=0xbbc9 || mask!=UINT32_MAX || value!=1200 || read(0xbbba)!=0x10a8 || !code_matches(read))return false;
    const uint32_t candidate=read(0xbbbc);if(!pool(candidate))return false;
    base=candidate;return true;
}
template<class Read>
bool complete(Read read,uint32_t base,uint32_t address,uint32_t value,uint32_t mask,uint32_t pc,uint32_t ar0) {
    if(!pool(base) || address!=base+1200*31 || address!=ar0 || value || mask!=UINT32_MAX ||
        pc!=0xbbd5 || read(0x10a8)!=base || read(0x10a9)!=1200 || !code_matches(read))return false;
    for(uint32_t i=0;i<1200;++i)if(read(base+i*31)!=base+(i+1)*31)return false;
    return true;
}

template<class Read>
bool scene_boundary(Read read,uint32_t frame,uint32_t ready,uint32_t address,uint32_t value,uint32_t mask,uint32_t pc) {
    return frame>=ready && address==0xff2 && value==UINT32_MAX && mask==UINT32_MAX && pc==0x67f6 &&
        read(0x67f5)==0x15200ff2 && read(0x681f)==0x082fbbb5 && read(0x6835)==0x082fbbb9;
}
}}
