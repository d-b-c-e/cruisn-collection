// SPDX-License-Identifier: BSD-3-Clause
#include <cstddef>
#include "exotica_bootstrap.h"
#include <cassert>
#include <vector>
int main() {
    namespace b=cruisn::exotica_bootstrap;
    std::vector<uint32_t> ram(0x40000);auto read=[&](uint32_t a){return ram.at(a);};
    size_t count=0;const auto *code=b::signatures(count);
    for(size_t i=0;i<count;++i)ram[code[i].first]=code[i].second;
    const uint32_t base=0x20000,tail=base+1200*31;
    ram[0xbbba]=0x10a8;ram[0xbbbc]=base;uint32_t selected=99;
    assert(b::begin(read,1200,UINT32_MAX,0xbbc9,selected) && selected==base);
    assert(!b::begin(read,1201,UINT32_MAX,0xbbc9,selected));
    assert(!b::complete(read,base,tail,0,UINT32_MAX,0xbbd5,tail));
    ram[0x10a8]=base;ram[0x10a9]=1200;
    for(uint32_t i=0;i<1200;++i)ram[base+i*31]=base+(i+1)*31;
    assert(b::complete(read,base,tail,0,UINT32_MAX,0xbbd5,tail));
    ram[base+701*31]++;
    assert(!b::complete(read,base,tail,0,UINT32_MAX,0xbbd5,tail));ram[base+701*31]--;
    assert(!b::complete(read,base,tail,1,UINT32_MAX,0xbbd5,tail));
    assert(!b::complete(read,base,tail,0,0xffff,0xbbd5,tail));
    assert(!b::complete(read,base,tail,0,UINT32_MAX,0xbbd4,tail));
    for(size_t i=0;i<count;++i) {
        ram[code[i].first]^=1;assert(!b::code_matches(read));
        assert(!b::complete(read,base,tail,0,UINT32_MAX,0xbbd5,tail));ram[code[i].first]^=1;
    }
    for(uint32_t bad:{0u,0xfffu,0x30000u,0x3ffffu,UINT32_MAX})assert(!b::pool(bad));
    ram[0x67f5]=0x15200ff2;ram[0x681f]=0x082fbbb5;ram[0x6835]=0x082fbbb9;
    assert(b::scene_boundary(read,1385,1385,0xff2,UINT32_MAX,UINT32_MAX,0x67f6));
    assert(!b::scene_boundary(read,1384,1385,0xff2,UINT32_MAX,UINT32_MAX,0x67f6));
    assert(!b::scene_boundary(read,1385,1385,0xff3,UINT32_MAX,UINT32_MAX,0x67f6));
    assert(!b::scene_boundary(read,1385,1385,0xff2,0,UINT32_MAX,0x67f6));
    assert(!b::scene_boundary(read,1385,1385,0xff2,UINT32_MAX,0xffff,0x67f6));
    assert(!b::scene_boundary(read,1385,1385,0xff2,UINT32_MAX,UINT32_MAX,0x67f5));
    for(uint32_t at:{0x67f5u,0x681fu,0x6835u}) {
        ram[at]^=1;assert(!b::scene_boundary(read,1385,1385,0xff2,UINT32_MAX,UINT32_MAX,0x67f6));ram[at]^=1;
    }
}
