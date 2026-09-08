// SPDX-License-Identifier: BSD-3-Clause
// Exotica2.4 CPU sphere visibility, not Zeus projection or guest simulation.
#pragma once
#include "world_distance.h"

namespace cruisn { namespace exotica_visibility {
using world_distance::word;
constexpr uint32_t table_base=0xeaab, original_index=4999, far_limit=204800;
constexpr uint32_t maximum_index=far_limit/16, margin=88;
constexpr word guards[]={
    {0x67c3,0x0087ff48},{0x67cc,table_base},{0x67da,far_limit},
    {0x67d1,0x07480000},{0x67d0,0x08000000},{0x67ce,0x087f8000},
    {0x687f,0x15420714},{0x6882,0x02420715},{0x6885,0x04e31387},
    {0x6886,0x54e31387},{0x6887,0x04a267da},{0x6888,0x6a2900e9},
    {0x6889,0x08110003},{0x688a,0x05c40715},{0x688b,0x07404300},
    {0x688f,0x01a267d1},{0x6890,0x6a2700e1},{0x6892,0x042367d1},
    {0x6894,0x6a2900dd},{0x6897,0x01a267d0},{0x6898,0x6a2700d9},
    {0x689b,0x042267ce},{0x689c,0x6a2900d5},{0x68a3,0x1a2667d9},
    {table_base+original_index,0xf851bf7b}};

inline bool code_matches(const uint32_t *ram,size_t words)
{
    if (!ram || words<0x40000) return false;
    for (auto const &w:guards) if (ram[w.address]!=w.value) return false;
    return true;
}

struct sample { bool valid=false; int32_t depth=0,radius=0; uint32_t index=0; bool far_rejected=false; };
inline sample read_sample(const uint32_t *ram,size_t words,uint32_t object,uint32_t depth_plus_radius)
{
    sample result;
    if (!ram || words<0x40000 || object<0x1000 || object+uint64_t(0x16)>=0x40000) return result;
    int32_t depth=int32_t(ram[object+0x14]),radius=int32_t(ram[object+0x15]);
    int64_t sum=int64_t(depth)+radius;
    if (radius<0 || radius>=10000000 || sum<0 || sum>INT32_MAX || uint32_t(sum)!=depth_plus_radius) return result;
    result.valid=true;result.depth=depth;result.radius=radius;
    result.index=depth>0 ? uint32_t(depth)/16 : 0;
    result.far_rejected=sum>far_limit;
    return result;
}

inline bool extends(sample const &s)
{ return s.valid && !s.far_rejected && s.index>original_index && s.index<=maximum_index; }

inline uint32_t reciprocal(uint32_t index)
{
    if (index<=original_index || index>maximum_index) return 0;
    // Same measured six-decimal tail as World/USA, restricted here to Exotica's
    // unchanged204800 far gate. 240000 is only the shared generator's capacity.
    return world_distance::reciprocal(index,240000);
}

inline bool projection_consumer(uint32_t pc,uint32_t ar3,uint32_t ir0)
{ return pc==0x688c && ar3==table_base && ir0==original_index; }
constexpr uint32_t wide_center=0x082c0000; // C31 344 =256+88
constexpr uint32_t wide_upper=0x092bc000;  // C31 687 =511+176
} }
