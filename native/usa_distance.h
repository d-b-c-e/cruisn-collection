// SPDX-License-Identifier: BSD-3-Clause
// USA 4.5 global projection and scenery residency experiment.
#pragma once
#include "world_distance.h"

namespace cruisn { namespace usa_distance {
using world_distance::word;
using world_distance::valid_far;
using world_distance::maximum_index;
using world_distance::reciprocal;
constexpr uint32_t original_far=80000, reciprocal_base=0xb2b3, first_extra=5000;
constexpr word clamps[]={{0xd0,0x04e30000},{0xd1,0x54e30000},
    {0x157,0x04f20000},{0x158,0x55720000},{0x1b1,0x04f20000},{0x1b2,0x55720000},
    {0x23b,0x04f20000},{0x23c,0x55720000},{0x277,0x04e00000},{0x278,0x55600000}};
constexpr word projection_sites[]={{0xd5,0x0741c300},{0x15d,0x24c00182},{0x15f,0xde180b82},
    {0x1b5,0x24c00182},{0x1b7,0xde380b82},{0x241,0x24c00182},{0x243,0xde180b82},
    {0x27c,0x24e0c3c2},{0x27f,0x24e0c3c2},{0xa728,0x07408200}};
constexpr word residency_sites[]={{0x729b,0x0824727d},{0x72af,0x1541011c},
    {0x72b1,0x18010004},{0x72b2,0x1841011d},{0x72b7,0x1ae03000},{0x72b8,0x1540010e},
    {0x7280,0x0824727e},{0x728e,0x1ae03000},{0x728f,0x1540010e}};
inline bool projection_pc(uint32_t pc)
{
    for (auto const &w:projection_sites) if (pc==w.address+1) return true;
    return false;
}
inline bool projection_base(uint32_t pc, uint32_t offset, uint32_t ar2, uint32_t ar3, uint32_t r5)
{
    if (!projection_pc(pc)) return false;
    if (pc==0xd6) return ar3==offset;
    if (pc==0x27d || pc==0x280) return r5==reciprocal_base && ar2==offset;
    return ar2==reciprocal_base;
}
inline bool code_matches(const uint32_t *ram, size_t words, uint32_t far)
{
    if (!ram || words<0x20000 || !valid_far(far) || ram[0x55]!=far || ram[0x52]!=reciprocal_base
        || ram[0xcb]!=0x04a30055 || ram[0xa727]!=0x082a0052 || ram[0xa725]!=0x0852041c
        || ram[0xa726]!=0x03f2fffc) return false;
    for (auto const &w:clamps) if (ram[w.address]!=(w.value|maximum_index(far))) return false;
    for (auto const &w:projection_sites) if (ram[w.address]!=w.value) return false;
    return true;
}
inline bool residency_matches(const uint32_t *ram, size_t words)
{
    if (!ram || words<0x20000 || ram[0x727d]!=75000 || ram[0x727e]!=80000) return false;
    for (auto const &w:residency_sites) if (ram[w.address]!=w.value) return false;
    return true;
}
inline uint32_t admission_limit(uint32_t far) { return far*15/16; }
} }
