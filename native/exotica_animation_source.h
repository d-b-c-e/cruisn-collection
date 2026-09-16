// SPDX-License-Identifier: BSD-3-Clause
// Standalone initial render-field reconstruction, not future-source admission.
#pragma once
#include "exotica_future_sections.h"

namespace cruisn { namespace exotica_animation {
// The caller supplies the actually allocated animation node. This routine does
// not prove its owner, choose a random phase, or call the guest allocator.
// B/C metadata can overwrite word24 after animation setup; A/F invokes a custom
// handler. Keep those paths excluded until their resulting semantics are known.
inline bool initial_fields(const std::array<uint32_t,6> &definition,
    const std::array<uint32_t,6> &model,const exotica_future::Section &section,
    const std::array<uint32_t,11> &constants,const std::array<uint32_t,7> &trig,
    const std::array<uint32_t,2> &materials,uint32_t node,exotica_future::Source &out)
{
    out=exotica_future::Source();
    const uint32_t type=definition[5]&0xf00;
    if(!(definition[0]>>24) || type==0xa00 || type==0xb00 || type==0xc00 || type==0xf00 ||
        node<0x1000 || uint64_t(node)+6>0x40000 || (node<0x32000 && node+6>0x30000))return false;
    auto plain=definition;plain[0]&=0xffffff;
    exotica_future::Source fields;
    if(!exotica_future::descriptor(plain,model,section,constants,trig,materials,fields) || !fields.supported)
        return false;
    fields.words[15]|=0x2000;fields.words[17]=definition[0];fields.words[24]=node;
    // Never mark this as a supported future source: phase and ownership are not
    // supplied by an initial-field calculation.
    fields.supported=false;out=fields;return true;
}
} }
