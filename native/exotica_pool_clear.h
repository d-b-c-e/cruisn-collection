// SPDX-License-Identifier: BSD-3-Clause
// Qualify the original global-clear loop which invalidates the scenery pool.
// No guest writes. The caller pairs head/count and commits reset at the tail.
#pragma once
#include <cstdint>

namespace cruisn { namespace exotica_pool_clear {
constexpr uint32_t first=0x471, end=0x11cc, instruction=0x85b3;
template<class Read>
bool valid(Read read,uint32_t address,uint32_t value,uint32_t mask,
           uint32_t pc,uint32_t r0,uint32_t ar0,uint32_t rc,uint32_t rs,uint32_t re) {
    if((address!=0x10a8 && address!=0x10a9 && address!=end-1) || value ||
       mask!=UINT32_MAX || pc!=instruction+1 || r0 || ar0!=address+1 ||
       rc!=end-1-address || rs!=instruction || re!=instruction)return false;
    const uint32_t code[]={0x082885a0,0x083b85a1,0x181b0008,0x187b0001,
                           0x1a800000,0x640085b3,0x15402001,0x78800000};
    if(read(0x85a0)!=first || read(0x85a1)!=end)return false;
    for(unsigned i=0;i<8;++i)if(read(0x85ad+i)!=code[i])return false;
    // Verify the completed prefix, not just a coincidental zero at the head.
    for(uint32_t p=first;p<address;++p)if(read(p))return false;
    return true;
}
} }
