// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_animation.h"
#include <cassert>
#include <iostream>
using namespace cruisn::exotica_animation;
int main()
{
    Sequence s;State a,b;
    const std::vector<uint32_t> words={0xa00100,0xa00200,0xfffffffe};
    assert(decode(0x03010002,words,s));
    a.remaining=3;a.cursor=2;a.model=0x12a00300;
    assert(step(s,a,b) && b.remaining==2 && b.cursor==2 && b.model==a.model);
    a=b;assert(step(s,a,b) && b.remaining==1 && b.cursor==2);
    a=b;assert(step(s,a,b) && b.remaining==3 && b.cursor==1 && b.model==words[0]);
    a.remaining=0;a.cursor=1;
    assert(step(s,a,b) && b.remaining==3 && b.cursor==2 && b.model==words[1]);
    for(uint32_t header:{0x00000002U,0x03000003U,0x03030002U})
        assert(!decode(header,words,s) && s.models.empty());
    auto bad=words;bad.back()=0xffffffff;assert(!decode(0x03010002,bad,s));
    bad=words;bad[0]|=0x1000000;assert(!decode(0x03010002,bad,s));
    assert(decode(0x03010002,words,s));
    a.remaining=4;assert(!step(s,a,b));
    a.remaining=1;a.cursor=3;assert(!step(s,a,b));
    a.cursor=0;a.model=0;assert(!step(s,a,b));
    std::cout<<"PASS animation countdown, wrap and rejection boundaries\n";
}
