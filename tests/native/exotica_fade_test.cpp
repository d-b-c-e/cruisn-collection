// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_fade.h"
#include <cassert>
#include <iostream>
int main()
{
    cruisn::ExoticaFadeStep out;
    assert(cruisn::exotica_fade_step(0x78081234,0x04000130,8,out));
    assert(out.packed==0x78101234 && out.flags==0x04000130 && !out.completed);
    assert(cruisn::exotica_fade_step(0x10f01234,0x04000130,8,out));
    assert(out.packed==0x04f81234 && out.flags==0x30 && out.completed);
    assert(cruisn::exotica_fade_step(0x05f61234,0x04008130,1,out));
    assert(out.packed==0x04f71234 && out.flags==0x8030 && out.completed);
    const auto saved=out;
    for(uint32_t increment:{0U,256U,0xffffffffU})
        assert(!cruisn::exotica_fade_step(0x78081234,0x04000130,increment,out));
    assert(!cruisn::exotica_fade_step(0x00fa1234,0x04000130,8,out));
    assert(!cruisn::exotica_fade_step(0x78081234,0x100,8,out));
    assert(out.packed==saved.packed && out.flags==saved.flags && out.completed==saved.completed);
    // A complete original cadence leaves metadata untouched and terminates once.
    uint32_t packed=0x7808abcd,flags=0x04008130;unsigned count=0;
    while(flags&0x04000000)
    {
        assert(++count<=30 && cruisn::exotica_fade_step(packed,flags,8,out));
        assert((out.packed&0xffff)==0xabcd && (out.flags&0x8000));
        packed=out.packed;flags=out.flags;
    }
    assert(count==30 && packed==0x04f8abcd && flags==0x8030);
    std::cout<<"PASS Exotica render fade boundaries and complete30-step cadence\n";
}
