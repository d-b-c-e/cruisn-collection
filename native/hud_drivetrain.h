// USA v4.5 drivetrain state, traced from the game's tach palette and gear HUD.
// Addresses are C31 word addresses. The RPM scale is an arcade presentation,
// not a claim that the original game's internal rev units are revolutions/minute.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstddef>

namespace cruisn {
struct Drivetrain {
    bool valid=false;
    uint32_t player=0;
    int gear=0;
    float rev=0, fraction=0, rpm=0;
};
using UsaDrivetrain = Drivetrain;

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

inline Drivetrain read_drivetrain(const uint32_t *ram, size_t words,
                                 uint32_t player, unsigned gear_offset,
                                 unsigned rev_offset, float fraction_per_rev)
{
    Drivetrain value;
    if (!ram || player<0x1000 || player>=words || words-player<=std::max(gear_offset,rev_offset)) return value;
    unsigned const gear=ram[player+gear_offset];
    float const rev=c31_drivetrain_float(ram[player+rev_offset]);
    if (gear>4 || !std::isfinite(rev) || rev<0 || rev>128) return value;
    value.valid=true;value.player=player;value.gear=int(gear);value.rev=rev;
    value.fraction=std::max(0.0f,std::min(1.0f,rev*fraction_per_rev));
    value.rpm=900.0f+7100.0f*value.fraction;
    return value;
}

// World 2.4 and 2.5 have separately verified code/data layouts. The caller
// must select the exact ROM; this is not an address scan or a clone fallback.
inline bool world_drivetrain_code(const uint32_t *ram, size_t words, bool v25)
{
    if (!ram || words<=0xee0e) return false;
    unsigned const code=v25?0x9acf:0x9ada, pointer=v25?0xee08:0xee0e;
    unsigned const gate=v25?0x99e5:0x99f0, state=v25?0xebdc:0xebe2;
    return ram[code]==(0x08280000|pointer) && ram[code+1]==0x07400052 &&
        ram[code+2]==0x0a60e6aa && ram[code+25]==0x08400051 &&
        ram[gate]==(0x08200000|state) && ram[gate+1]==0x04e00005 &&
        ram[gate+3]==0x04e00004 && ram[gate+8]==0x084a0051;
}
inline Drivetrain world_drivetrain(const uint32_t *ram, size_t words, bool v25)
{
    if (!world_drivetrain_code(ram,words,v25)) return {};
    unsigned const state=ram[v25?0xebdc:0xebe2];
    if (state!=4 && state!=5) return {}; // same lifetime gate as the tach HUD
    return read_drivetrain(ram,words,ram[v25?0xee08:0xee0e],0x51,0x52,0.458251953125f/22.0f);
}
inline bool world_driving(const uint32_t *ram, size_t words, bool v25)
{
    return world_drivetrain_code(ram,words,v25) && ram[v25?0xebdc:0xebe2]==4 &&
        (ram[v25?0xebdd:0xebe3]&4)!=0;
}

inline bool exotica_drivetrain_code(const uint32_t *ram, size_t words)
{
    return ram && words>0xc323 && ram[0xc2ac]==0x082810be && ram[0xc2ad]==0x084a0062 &&
        ram[0xc2c0]==0x082810be && ram[0xc2c1]==0x07400063 && ram[0xc2c2]==0x0a60f2ac &&
        ram[0xc285]==0x08200076 && ram[0xc286]==0x78850000 &&
        ram[0x3c1b]==0x0a60e7ae && ram[0x3c1d]==0x15201074;
}
inline Drivetrain exotica_drivetrain(const uint32_t *ram, size_t words)
{
    if (!exotica_drivetrain_code(ram,words) || ram[0x76]!=1) return {};
    return read_drivetrain(ram,words,ram[0x10be],0x62,0x63,0.6669921875f/32.0f);
}
inline int exotica_hud_mph(const uint32_t *ram, size_t words)
{
    if (!exotica_drivetrain(ram,words).valid || ram[0x1074]>400) return -1;
    // Unconverted MPH buffer. The display optionally converts it to metric;
    // Forza always needs m/s, regardless of the cabinet's display units.
    return int(ram[0x1074]);
}

inline bool offroad_drivetrain_code(const uint32_t *ram, size_t words)
{
    // Off Road's C code addresses globals with DP=1, unlike USA/World.
    return ram && words>0x1c86c && ram[0xabed]==0x082cc86c && ram[0xabee]==0x0aec00bc &&
        ram[0xabef]==0x022c9d25 && ram[0xaca7]==0x07420436 && ram[0xaca8]==0x0a229d6b &&
        ram[0xad9b]==0x0852040b && ram[0xad7f]==0x07209d11 && ram[0xad84]==0x0a229d77 &&
        ram[0xad91]==0x050a0002 && ram[0xad97]==0x6200a5cc && ram[0x19d6b]==0xf303126f;
}
inline Drivetrain offroad_drivetrain(const uint32_t *ram, size_t words)
{
    Drivetrain value;
    if (!offroad_drivetrain_code(ram,words) || ram[0x1c86c]>=8) return value;
    uint64_t const p=uint64_t(ram[0x19d25])+0xbc*ram[0x1c86c];
    if (p<0x1000 || p>=words || words-p<=0x36) return value;
    int const gear=int32_t(ram[p+0xb]);
    float const rev=c31_drivetrain_float(ram[p+0x36]);
    // Neutral/reverse (-1) is represented as unknown/neutral on the legacy
    // Forza gear field; forward gears come from the actual drivetrain.
    if (gear< -1 || gear>4 || !std::isfinite(rev) || rev<0 || rev>16000) return value;
    value.valid=true;value.player=uint32_t(p);value.gear=std::max(0,gear);value.rev=rev;
    value.fraction=std::min(1.0f,rev*0.0001250000059371814f);
    value.rpm=900.0f+7100.0f*value.fraction;
    return value;
}
inline int offroad_hud_mph(const uint32_t *ram, size_t words)
{
    if (!offroad_drivetrain_code(ram,words) || ram[0x19d0c]>1) return -1;
    // Read the already-smoothed value consumed by AD91's integer formatter.
    float const shown=c31_drivetrain_float(ram[0x19d11])*c31_drivetrain_float(ram[0x19d77]);
    if (!std::isfinite(shown) || shown<0 || shown>640) return -1;
    int const digits=int(shown);
    return ram[0x19d0c]?digits:int(float(digits)/1.609344f+0.5f);
}
}
