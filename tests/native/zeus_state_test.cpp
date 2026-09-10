// SPDX-License-Identifier: BSD-3-Clause
#include "zeus_state.h"
#include <cassert>
int main()
{
    using namespace cruisn::zeus_state;
    Context c;Result r;const std::vector<uint32_t> packet={0x16000000,0x80000000,0x80000000,0x80000000};
    assert(transition(c,{0x36200000,0x150007ff},packet,123,r));
    assert(c.render[0x15]==0 && r.context.render[0x15]==2047 && r.context.regs[8]==123);
    assert(r.context.regs[0x18]==6 && r.context.regs[0x19]==2);
    r.context.texture=456;
    auto reset=packet;reset.insert(reset.begin(),{0x05200000,0x15000000});
    assert(transition(r.context,{},reset,1,r) && r.context.render[0x15]==0 && r.context.texture==456);
    assert(!transition(c,{0x36200000,0x08000001},packet,1,r));
    assert(!transition(c,{0x38000000,0},packet,1,r));
    assert(!transition(c,{},std::vector<uint32_t>{0x07000000,0,0,0},1,r));
    assert(floating(cruisn::scenery::Float::integer(-10).store())==-10.0f);
}
