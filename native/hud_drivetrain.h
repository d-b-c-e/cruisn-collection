// USA v4.5 drivetrain state, traced from the game's tach palette and gear HUD.
// Addresses are C31 word addresses. The RPM scale is an arcade presentation,
// not a claim that the original game's internal rev units are revolutions/minute.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstddef>

namespace cruisn {
struct UsaDrivetrain {
    bool valid=false;
    uint32_t player=0;
    int gear=0;
    float rev=0, fraction=0, rpm=0;
};

inline float c31_drivetrain_float(uint32_t word)
{
    int const exponent=int32_t(word)>>24;
    if (word == 0x80000000) return 0.0f;
    float const mantissa=float(word&0x7fffff)/8388608.0f;
    return std::ldexp((word&0x800000 ? -2.0f : 1.0f)+mantissa,exponent);
}

inline UsaDrivetrain usa_drivetrain(const uint32_t *ram, size_t words)
{
    UsaDrivetrain value;
    if (!ram || words<=0xe8a8 || ram[0x9e53]!=0x0828e8a8 ||
        ram[0x9e54]!=0x07400039 || ram[0x9e55]!=0x0a60e6aa ||
        ram[0x9e6b]!=0x08400038 || ram[0x9d87]!=0x084a0038)
        return value;
    uint32_t const player=ram[0xe8a8];
    if (player<0x1000 || player>=words || words-player<=0x39) return value;
    uint32_t const gear=ram[player+0x38];
    float const rev=c31_drivetrain_float(ram[player+0x39]);
    // The HUD clamps its fill to 22 entries. Physics includes revs above the
    // 47-unit free-rev limit; accept a bounded overshoot, never arbitrary RAM.
    if (gear>4 || !std::isfinite(rev) || rev<0 || rev>128) return value;
    value.valid=true;value.player=player;value.gear=int(gear);value.rev=rev;
    // Exact short-float multiplier from 9E55; preserve smooth sub-segment revs.
    value.fraction=std::max(0.0f,std::min(1.0f,rev*0.458251953125f/22.0f));
    value.rpm=900.0f+7100.0f*value.fraction;
    return value;
}
}
