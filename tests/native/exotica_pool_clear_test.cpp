#include "../../native/exotica_pool_clear.h"
#include <array>
#include <cassert>
using namespace cruisn::exotica_pool_clear;
int main() {
    std::array<uint32_t,0x10000> ram{};
    ram[0x85a0]=first;ram[0x85a1]=end;
    const uint32_t code[]={0x082885a0,0x083b85a1,0x181b0008,0x187b0001,
                          0x1a800000,0x640085b3,0x15402001,0x78800000};
    for(unsigned i=0;i<8;++i)ram[0x85ad+i]=code[i];
    auto read=[&](uint32_t p){return ram[p];};
    auto check=[&](uint32_t a,uint32_t pc,uint32_t ar,uint32_t rc,uint32_t rs,uint32_t re) {
        return valid(read,a,0,UINT32_MAX,pc,0,ar,rc,rs,re);
    };
    for(uint32_t a:{0x10a8U,0x10a9U,end-1}) {
        assert(check(a,instruction+1,a+1,end-1-a,instruction,instruction));
        assert(!check(a,instruction,a+1,end-1-a,instruction,instruction));
        assert(!check(a,instruction+1,a,end-1-a,instruction,instruction));
        assert(!check(a,instruction+1,a+1,end-a,instruction,instruction));
        assert(!check(a,instruction+1,a+1,end-1-a,instruction-1,instruction));
        assert(!check(a,instruction+1,a+1,end-1-a,instruction,instruction+1));
        assert(!valid(read,a,1,UINT32_MAX,instruction+1,0,a+1,end-1-a,instruction,instruction));
        assert(!valid(read,a,0,0xffff,instruction+1,0,a+1,end-1-a,instruction,instruction));
        assert(!valid(read,a,0,UINT32_MAX,instruction+1,1,a+1,end-1-a,instruction,instruction));
        ram[first]=1;assert(!check(a,instruction+1,a+1,end-1-a,instruction,instruction));ram[first]=0;
        ram[0x85b3]^=1;assert(!check(a,instruction+1,a+1,end-1-a,instruction,instruction));ram[0x85b3]^=1;
    }
    assert(!check(0x10a7,instruction+1,0x10a8,end-1-0x10a7,instruction,instruction));
}
