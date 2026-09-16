#include "offroad_billboard_source.h"
#include <cassert>
int main()
{
    using cruisn::offroad_billboard_source::descriptor;
    std::array<uint32_t,11> d{};d[0]=0x800804;d[1]=0xc01000;d[3]=67U<<16;
    const std::array<uint32_t,3> binding={{0xc02000,100,200}};
    bool supported;std::array<uint32_t,22> output;
    assert(descriptor(d,7,2,10,binding,67,0,supported,output) && supported);
    assert(output[5]==d[0] && output[6]==0x07078000 && output[17]==binding[0]);
    assert(descriptor(d,7,2,10,binding,67,8,supported,output) && !supported);
    assert((output==std::array<uint32_t,22>{}));
    assert(!descriptor(d,7,2,10,binding,68,0,supported,output));
    for(uint32_t flags:{0x04004004U,0x10000804U,0x804U|2U}) {
        d[0]=flags;assert(descriptor(d,7,2,10,binding,67,0,supported,output) && !supported);
    }
    d[0]=0x804;assert(descriptor(d,7,2,10,binding,0,~0U,supported,output) && supported);
    assert(!descriptor(d,7,10,10,binding,0,0,supported,output));
    d[1]=0x1ffff;assert(!descriptor(d,7,2,10,binding,0,0,supported,output));
}
