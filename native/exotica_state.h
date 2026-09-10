// SPDX-License-Identifier: BSD-3-Clause
// Exotica2.4 CPU-side object setup. All operands/caches are private, no guest cycles.
// The light branch inherits depth register15; this is not a self-contained context.
#pragma once
#include "scenery_c31.h"
#include <vector>
namespace cruisn { namespace exotica_state {
struct Operands
{
    std::array<uint32_t,32> object{};
    uint32_t flags=0,palette_setup=0;
    std::array<uint32_t,3> cache{};
    std::array<uint32_t,12> constants{};
    std::array<uint32_t,46> commands{};
    std::array<uint32_t,4> programs{};
    std::array<std::array<uint32_t,4>,4> bodies{};
    std::vector<uint32_t> defaults;
};
enum class Branch { Cached, Light, Fade, Flag400, Flag200, Default };
struct Result
{
    std::vector<uint32_t> packet;
    std::array<uint32_t,3> cache{};
    Branch branch=Branch::Cached;
    int program=-1;
};
inline bool setup(const Operands &a,Result &output)
{
    output=Result();Result r;r.cache=a.cache;
    const auto c=[&](unsigned p){return a.constants[p-0x67d0];};
    const auto w=[&](unsigned p){return a.commands[p-0xb479];};
    if(a.defaults.empty() || a.defaults.size()>16 || !c(0x67d6) ||
        w(0xb47b)!=0x32000000 || w(0xb47c)!=0x1c000000 ||
        w(0xb481)!=0x05410000 || w(0xb482)!=0x05400000 || w(0xb493)!=0x05200000)return false;
    for(const auto &b:a.bodies)if(b[0]!=0x05410000 || b[2]!=0x05400000)return false;
    auto &v=r.packet;
    const auto pointer=[&](uint32_t value){v.push_back(w(0xb493));v.push_back(value);};
    const uint32_t flags=a.flags,key=(flags&c(0x67d2))|(a.object[16]&0xffff0000);
    // Cache invalidation executes in 68D1's delay slots on both branch outcomes.
    r.cache[2]=(flags&0x800)?0xffffffff:key;
    if(key!=a.cache[2])
    {
        r.program=(flags&0x8000)?2:0;
        if(flags&0x4000)r.program=1;
        if((flags&c(0x67d6))==c(0x67d6))r.program=3;
        if(a.programs[r.program]!=a.cache[1])
        {
            r.cache[1]=a.programs[r.program];v.push_back(w(0xb47b));
            v.insert(v.end(),a.bodies[r.program].begin(),a.bodies[r.program].end());
        }
        const uint32_t high=a.object[16]>>16;
        if((flags&c(0x67d6))==c(0x67d6))
        {
            using scenery::Float;
            r.branch=Branch::Light;pointer(w(0xb4a1));pointer(w(0xb498));pointer(w(0xb4a6)|((high>>8)<<1));
            v.push_back(w(0xb47c));v.push_back(Float::integer(10).store());
            v.push_back((-Float::integer(5)*Float::load(0xff000000)).store());
            v.push_back((Float::integer(high&255)*Float::load(c(0x67d7))).store());
        }
        else if(flags&0x100)
        {
            r.branch=Branch::Fade;pointer(w(0xb49d)|0x7ff);pointer(w(0xb4a0));
            pointer(w(0xb4a4)|(high&255));pointer(w(0xb4a6)|((high>>8)<<1));
            pointer(w((flags&8)?0xb499:0xb498));
        }
        else if(flags&0x400){r.branch=Branch::Flag400;pointer(c(0x67d3));pointer(w(0xb498));}
        else if(flags&0x200){r.branch=Branch::Flag200;pointer(c(0x67d4));pointer(c(0x67d5));}
        else
        {
            r.branch=Branch::Default;
            for(auto value:a.defaults)pointer(value);
            pointer(w(0xb49d));
        }
    }
    if(a.object[18]!=a.cache[0])
    {
        r.cache[0]=a.object[18];
        for(auto value:{w(0xb47b),w(0xb481),a.object[18],w(0xb482),a.palette_setup})v.push_back(value);
    }
    output=std::move(r);return true;
}
} }
