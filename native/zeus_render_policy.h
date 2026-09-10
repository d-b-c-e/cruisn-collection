// SPDX-License-Identifier: BSD-3-Clause
// copyright-holders:Aaron Giles
// Isolated semantics from mamedev/mame#16094, head54b7ec0720e1 (mourix).
// Mask0 preserves legacy recordings; bits1/2/4 select depth/alpha/blend trials.
#pragma once
#include <algorithm>
#include <cstdint>
namespace cruisn { namespace zeus_policy {
enum : uint32_t { DepthFloor=1, AlphaDepth=2, BlendFields=4, QuadDepthFloor=512 };
struct Material { bool blend,depth_test,depth_write;uint32_t source_alpha; };
inline Material material(uint32_t mask,uint32_t mode,uint32_t depth,uint32_t blend,uint32_t source)
{
    const bool alpha=(mode&3)==2 && (mode&0x80);
    Material r;
    r.blend=((mask&BlendFields)?(blend&0x02ff00)==0x020200:blend==0x020202) ||
        (blend==0x021e0e && (mode&3)==2);
    r.source_alpha=((mask&BlendFields) && (blend&255)==4)?256:std::min(source,256U);
    r.depth_test=!(depth&0x20) && (!alpha || (mask&AlphaDepth));
    r.depth_write=!(depth&0x1000) && (!alpha || (mask&AlphaDepth));
    return r;
}
inline int32_t depth(uint32_t mask,int32_t z,int32_t minimum)
{
    return mask&DepthFloor?std::max(z,minimum):z+minimum;
}
} }
