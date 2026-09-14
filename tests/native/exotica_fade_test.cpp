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
    for(uint32_t flags:{0U,0x100U,0x8100U,0x80000130U}) {
        assert(cruisn::exotica_finish_marked_fade(0x55121234,flags,out));
        assert(out.packed==0x55121234 && out.flags==flags && !out.completed);
    }
    assert(cruisn::exotica_finish_marked_fade(0x7808abcd,0x04008130,out));
    assert(out.packed==0x04f8abcd && out.flags==0x8030 && out.completed);
    assert(cruisn::exotica_finish_marked_fade(0x00f61234,0x04000130,out));
    assert(out.packed==0x01fe1234 && out.flags==0x30 && out.completed);
    const auto finished=out;
    for(uint32_t alpha=247;alpha<=255;++alpha) {
        assert(!cruisn::exotica_finish_marked_fade(alpha<<16,0x04000130,out));
        assert(out.packed==finished.packed && out.flags==finished.flags && out.completed);
    }
    for(uint32_t alpha=0;alpha<247;++alpha) {
        const uint32_t initial=0x7f001357|(alpha<<16);
        assert(cruisn::exotica_finish_marked_fade(initial,0x04008130,out));
        auto actual=initial;uint32_t flags=0x04008130;cruisn::ExoticaFadeStep expected;
        do {assert(cruisn::exotica_fade_step(actual,flags,8,expected));actual=expected.packed;flags=expected.flags;} while(!expected.completed);
        assert(out.packed==expected.packed && out.flags==expected.flags && out.completed);
    }
    std::cout<<"PASS Exotica render fade boundaries and complete30-step cadence\n";
}
