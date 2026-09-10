// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_state.h"
#include <cassert>
#include <algorithm>
int main()
{
    using namespace cruisn::exotica_state;
    Operands a;
    auto w=[&](unsigned p,uint32_t v){a.commands[p-0xb479]=v;};
    w(0xb47b,0x32000000);w(0xb47c,0x1c000000);w(0xb481,0x05410000);w(0xb482,0x05400000);
    w(0xb493,0x05200000);w(0xb498,0x14004000);w(0xb49d,0x15000000);w(0xb4a1,0x40020204);w(0xb4a6,0x0d000000);
    a.constants[2]=0xc700;a.constants[6]=0x8100;a.constants[7]=0xff000000;
    for(unsigned i=0;i<4;++i){a.programs[i]=i+10;a.bodies[i]={{0x05410000,i+100,0x05400000,0x50000}};}
    a.defaults={0x40000000,0x14004000};a.cache={{0,10,0xffffffff}};
    Result r;assert(setup(a,r));assert(r.packet.back()==0x15000000);assert(a.cache[2]==0xffffffff);
    a.cache=r.cache;assert(setup(a,r) && r.packet.empty());
    a.flags=0x8100;assert(setup(a,r) && r.branch==Branch::Light && r.program==3);
    assert(std::find(r.packet.begin(),r.packet.end(),0x15000000)==r.packet.end());
    a.flags=0x800;a.cache[2]=0;assert(setup(a,r) && r.cache[2]==0xffffffff && r.branch==Branch::Cached);
    a.defaults.clear();assert(!setup(a,r) && r.packet.empty());
}
