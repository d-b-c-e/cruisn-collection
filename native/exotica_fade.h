// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstdint>
namespace cruisn {
struct ExoticaFadeStep { uint32_t packed=0, flags=0; bool completed=false; };
// Verified B73D..B74D render-field update, before subsequent list classification.
// Inputs outside a positive, non-overflowing eight-bit alpha step are rejected.
inline bool exotica_fade_step(uint32_t packed, uint32_t flags, uint32_t increment,
    ExoticaFadeStep &out)
{
    const uint32_t alpha=(packed>>16)&255;
    if (!(flags&0x04000000) || !increment || increment>255 || alpha+increment>255)
        return false;
    const uint32_t next=alpha+increment;
    ExoticaFadeStep value;
    value.packed=((((256-next)>>1)<<8)|next)<<16 | (packed&65535);
    value.completed=next>=247;
    value.flags=value.completed ? flags&~uint32_t(0x04000100) : flags;
    out=value;return true;
}
// Offline endpoint experiment, NOT a temporal handover policy. Only the game's
// explicit marker grants permission to complete a fade. Bit0x100 alone may
// describe intrinsic blending. Reject marked operands past completion.
inline bool exotica_finish_marked_fade(uint32_t packed,uint32_t flags,ExoticaFadeStep &out)
{
    if(!(flags&0x04000000)) {
        ExoticaFadeStep value;value.packed=packed;value.flags=flags;
        out=value;return true;
    }
    const uint32_t alpha=(packed>>16)&255;
    if(alpha>=247)return false;
    // Collapse the measured +8 cadence to its first completing step, including
    // its destination coefficient and preserved low-word metadata.
    return exotica_fade_step(packed,flags,8*((247-alpha+7)/8),out);
}
}
