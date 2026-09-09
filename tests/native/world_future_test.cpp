#include "world_future_sections.h"
#include <cassert>
#include <map>
#include <stdexcept>
int main()
{
    using namespace cruisn;
    auto f=[](int n){return scenery::Float::integer(n).store();};
    std::map<uint32_t,uint32_t> m={{0xd575,0xc10000},{0xd5a5,0},{0xd5a1,0},
        {0x4151,0x1000},{0x4150,0x2000},{0x1000,256},{0x2001,16},
        {0xc00000,0},{0xc00001,1},{0xc00002,100}};
    uint32_t constants[]={4263704963U,4118653474U,3979254875U,4088417758U,4178085694U,4258616668U,4788187U};
    for(unsigned i=0;i<7;++i)m[0xcc35+i]=constants[i];
    uint32_t section[]={8,f(100),f(200),f(300),f(0),0xc20000,0xc20020,0xc20030,f(1),f(2),f(3),0};
    for(unsigned i=0;i<12;++i)m[0xc10000+i]=section[i];
    for(unsigned i=0;i<8;++i)m[0xc1000c+i]=0;
    m[0xc1000c]=UINT32_MAX;
    for(auto list:{0xc20000U,0xc20020U,0xc20030U})
    {
        unsigned count=list==0xc20000?2:1;m[list]=0;m[list+1]=count;
        for(unsigned j=0;j<count;++j)
        {uint32_t definition[]={0xc00002,10,20,30,f(0),0xfff00000};
         for(unsigned k=0;k<6;++k)m[list+2+6*j+k]=definition[k];}
    }
    auto read=[&](uint32_t p){auto i=m.find(p);if(i==m.end())throw std::runtime_error("unexpected read");return i->second;};
    const auto before=m;
    world_future::Cache cache;world_future::Stats stats;std::vector<world_host::Descriptor> objects;
    assert(world_future::collect(read,cache,objects,stats) && objects.size()==4 && stats.new_sections==2);
    assert(objects[0].words[1]==f(111) && objects[0].words[2]==f(222) && objects[0].words[3]==f(333));
    assert(objects[3].words[1]==f(110) && objects[3].words[2]==f(220) && objects[3].words[3]==f(330));
    for(const auto &o:objects)assert(o.words[16]==256 && o.words[17]==16);
    std::vector<world_host::Descriptor> warm;world_future::Stats warm_stats;
    assert(world_future::collect(read,cache,warm,warm_stats) && warm_stats.new_sections==0 && m==before);
    for(size_t i=0;i<warm.size();++i)assert(warm[i].id==objects[i].id && warm[i].words==objects[i].words);
    // A warm cache must not retain excluded roads after a diagnostic toggle.
    m[0xc20007]=0xfff01b00;cache.clear();objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.size()==3 && stats.special==1);
    objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats,64,true) && objects.size()==4);
    assert(objects[0].words[15]==0x1300 && objects[0].words[14]==0x10002001);
    assert(objects[0].words[27]==(0xc10000|(1U<<24)));
    for(unsigned i=22;i<27;++i)assert(objects[0].words[i]==0); // no physics links
    objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.size()==3);
    m[0xc20007]=0xfff00000;cache.clear();
    m[0xd5a5]=1;m[0xd5a1]=0xc20008;objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.size()==3 && stats.skipped==1);
    m[0xd5a5]=2;m[0xd5a1]=0xc20022;objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.size()==2 && stats.skipped==2);
    m[0xd5a1]=0xc20023;objects.clear();stats={};
    assert(!world_future::collect(read,cache,objects,stats));
    m[0xd5a5]=0;m[0x1000]=UINT32_MAX;objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.empty() && stats.unbound==4);
    m[0xc10005]=0x993000;cache.clear();objects.clear();stats={};
    assert(!world_future::collect(read,cache,objects,stats));
    m[0xd575]=0;cache.clear();objects.clear();stats={};
    assert(world_future::collect(read,cache,objects,stats) && objects.empty() && cache.sections.empty());
}
