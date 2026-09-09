#include "usa_host_scenery.h"
#include <cassert>
#include <map>
#include <stdexcept>
int main()
{
    using namespace cruisn::usa_host;
    auto f=[](int n){return Float::integer(n).store();};
    std::map<uint32_t,uint32_t> memory={{0x41,0xc9b4},{0x45,0x809800},{0x47,0x809809},
        {0x4d,0x80982d},{0x4e,0x8099db},{0x52,0xb2b3},{0x54,f(200)},{0x62,0xea7c},
        {0xc8f5,4},{0xe8a1,1},{0xc9b4,0x10000},{0xb2b3+64,f(1)}};
    for(unsigned i=0;i<3;++i)memory[0x809800+i]=f(0);
    for(unsigned i=0;i<9;++i)memory[0x809809+i]=memory[0x80982d+i]=f(i%4==0?1:0);
    for(unsigned i=0;i<4;++i)memory[0x8099db+i]=f(i%3==0?1:0);
    for(unsigned i=0;i<32;++i)memory[0x10000+i]=0;
    for(unsigned i=0;i<9;++i)memory[0x10004+i]=f(i%4==0?1:0);
    memory[0x10001]=memory[0x10002]=f(0);memory[0x10003]=f(1024);
    memory[0x1000d]=0xc00000;memory[0x1000e]=0x2400;memory[0x10010]=0x200;
    const uint32_t model[]={20,3,0xfff6fff6,0,0xfff6000a,0,0x000a000a,0,0x000afff6,0,
        0x200100,0x03020100,0x00100000,0x10001010,0x20};
    for(unsigned i=0;i<sizeof(model)/4;++i)memory[0xc00000+i]=model[i];
    auto read=[&](uint32_t p){auto it=memory.find(p);if(it==memory.end())throw std::runtime_error("unexpected read");return it->second;};
    const auto before=memory;
    Scene scene;
    assert(build(read,scene) && scene.pending==1 && scene.decoded==1 && scene.objects.size()==1);
    const Quad expected={{0x100,0x200,246,189,266,189,266,210,246,210,0,16,4112,4096,0x20,0}};
    assert(scene.objects[0].quads.size()==1 && scene.objects[0].quads[0]==expected && memory==before);
    // Extended projection is host-owned; the callback has no guest tail words.
    memory[0x10003]=f(160016);
    assert(build(read,scene,80000) && scene.objects.empty());
    assert(build(read,scene,160000) && scene.projection==1 && scene.objects.empty());
    assert(build(read,scene,240000) && scene.decoded==1);
    memory[0x1000e]=0x1400;
    assert(!build(read,scene) && scene.objects.empty());
    memory[0x1000e]=0x2c00;
    assert(build(read,scene) && scene.unsupported==1 && scene.objects.empty());
    memory[0x10000]=0x10000;
    assert(!build(read,scene) && scene.objects.empty());
    memory[0x10000]=0;memory[0x1000e]=0x2400;memory[0x10003]=f(1024);memory[0x1000d]=0x993000;
    assert(!build(read,scene) && scene.objects.empty());
    memory[0x1000d]=0xc00000;memory[0x45]=0x993000;
    assert(!build(read,scene));
    assert(!build(read,scene,100000));
}
