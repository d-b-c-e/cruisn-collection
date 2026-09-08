#include "world_host_scenery.h"
#include <cassert>
#include <map>
#include <stdexcept>
int main()
{
    using cruisn::scenery::Float;
    auto f=[](int n){return Float::integer(n).store();};
    std::map<uint32_t,uint32_t> ram={{0x41,0xd4b7},{0x43,0x8099db},{0x48,0x809a04},
        {0x47,0x8099f7},{0x4d,0xb66f},{0x61ec,0x1000},{0x1000,0x10800},
        {0x8099f9,f(256)},{0x8099fa,f(200)},{0xb66f+64,f(1)}};
    for(int i=0;i<3;++i)ram[0xd4b7+i]=f(0);
    for(int i=0;i<9;++i)ram[0x8099db+i]=ram[0x809a04+i]=f(i%4==0?1:0);
    for(int i=0;i<32;++i)ram[0x10800+i]=0;
    ram[0x10801]=ram[0x10802]=f(0);ram[0x10803]=f(1024);
    ram[0x1080d]=0xc00000;ram[0x1080e]=0x2008;
    ram[0x10810]=0x200;ram[0x10811]=0x40;
    uint32_t model[]={20,0xc00100,4,0xfff6fff6,0,0xfff6000a,0,0x000a000a,0,0x000afff6,0,0x100,0x03020100};
    for(unsigned i=0;i<sizeof(model)/4;++i)ram[0xc00000+i]=model[i];
    ram[0xc00100]=0x00100000;ram[0xc00101]=0x10001010;ram[0xc00102]=0x20;
    bool io_read=false;
    auto read=[&](uint32_t p)->uint32_t{
        if(p>=0x900000 && p<0xc00000)io_read=true;
        auto i=ram.find(p);if(i==ram.end())throw std::runtime_error("unexpected read");
        return i->second;
    };
    cruisn::world_host::Scene good;
    assert(cruisn::world_host::build(read,good));
    assert(good.pending==1 && good.decoded==1 && good.objects.size()==1 && good.objects[0].quads.size()==1);
    cruisn::world_host::Quad expected={{0x100,0x200,246,189,266,189,266,210,246,210,0,16,4112,4096,0x60,0}};
    assert(good.objects[0].quads[0]==expected);
    ram[0x1080d]=0x993000;
    cruisn::world_host::Scene corrupt;
    assert(!cruisn::world_host::build(read,corrupt) && !io_read);
    ram[0x1080d]=0xc00000;ram[0x10800]=0x10800;
    cruisn::world_host::Scene cycle;
    assert(!cruisn::world_host::build(read,cycle));
    ram[0x10800]=0;ram[0x1080e]=0x2001;
    cruisn::world_host::Scene dynamic;
    assert(cruisn::world_host::build(read,dynamic) && dynamic.unsupported==1 && dynamic.objects.empty());
}
