#include "world_host_scenery.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn::world_host;
    const auto f=[](int v){return Float::integer(v).store();};
    std::map<uint32_t,uint32_t> ram={{0x41,0xd4b7},{0x43,0x8099db},{0x48,0x809a04},
        {0x47,0x8099f7},{0x4d,0xb66f},{0x61ec,0x1000},{0x1000,0},
        {0x8099f9,f(256)},{0x8099fa,f(200)},{0xb66f+64,f(1)},{0xd4c0,20000}};
    for(int i=0;i<3;++i)ram[0xd4b7+i]=f(0);
    for(int i=0;i<9;++i)ram[0x8099db+i]=ram[0x809a04+i]=f(i%4==0?1:0);
    Descriptor d;d.id=0xc0001100;d.active_margin=true;
    d.words[1]=f(-600);d.words[2]=f(0);d.words[3]=f(1024);
    for(int i=0;i<9;++i)d.words[4+i]=f(i%4==0?1:0);
    d.words[13]=0xc00000;d.words[14]=0x1001;
    uint32_t model[]={60,0xc00100,5,0xfff6fff6,0,0xfff6000a,0,0x000a000a,0,0x000afff6,0,
        0, uint32_t(-100),0x100,0x03020100};
    for(unsigned i=0;i<sizeof(model)/4;++i)ram[0xc00000+i]=model[i];
    ram[0xc00100]=0x00100000;ram[0xc00101]=0x10001010;ram[0xc00102]=0x20;
    auto read=[&](uint32_t p){auto i=ram.find(p);assert(i!=ram.end());return i->second;};
    std::vector<Descriptor> descriptors{d};Scene scene;
    const auto original=ram;
    // An unused near vertex must not reject a separate wholly valid polygon.
    assert(build(read,scene,80000,&descriptors,true));
    assert(scene.objects.size()==1 && scene.objects[0].quads.size()==1);
    assert(scene.objects[0].margin_only);
    for(unsigned i=2;i<10;i+=2)assert(int16_t(scene.objects[0].quads[0][i])<0);
    assert(ram==original);
    // Any referenced invalid vertex rejects that polygon, never a clamped draw.
    ram[0xc0000e]=0x04020100;Scene crossing;
    assert(build(read,crossing,80000,&descriptors,true));
    assert(crossing.objects.size()==1 && crossing.objects[0].quads.empty());
    // Future/pending behavior remains whole-model rejection.
    ram[0xc0000e]=0x03020100;descriptors[0].active_margin=false;
    descriptors[0].id=0x80000001;descriptors[0].words[14]=0x2001;Scene pending;
    assert(build(read,pending,80000,&descriptors,true) && pending.objects.empty());
}
