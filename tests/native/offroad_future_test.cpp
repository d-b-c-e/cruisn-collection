#include "offroad_future_sections.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn::offroad_future;
    std::map<uint32_t,uint32_t> m;
    auto read=[&](uint32_t p){return m[p];};
    Result r;assert(build(read,r) && r.frontier.pretrack);
    const uint32_t base=0xc00000,data=0xc01000;
    m[0x1b4b4]=base;m[0x1b4cc]=3;m[0x1b4bd]=1;
    m[0x1b4b5]=m[0x1b4b7]=m[0x1b4ba]=base;
    m[0x1b4cd]=0xc03000;m[0x1b4cf]=0x1200;m[0x1b4ce]=0x3210;
    for(unsigned i=0;i<3;++i)
    {m[base+4*i]=(i==0?1:i==2?0x80000000:0);m[base+4*i+1]=i;m[base+4*i+3]=data+64*i;
        m[data+64*i+16]=1;m[data+64*i+17]=0x20;m[data+64*i+18]=0xc02000;}
    assert(build(read,r) && r.sources.size()==2 && r.sources[0].words[6]==0x18000);
    const auto original=r.sources[0].words;
    Cache cache;assert(collect(read,r,cache));
    m[0x1b4cf]=0x2300;assert(collect(read,r,cache) && r.sources[0].words[18]==0x2300 && original[18]==0x1200);
    m[0x1b4b9]=1;assert(collect(read,r,cache) && r.sources.size()==1 && r.sources[0].number==2);
    m[0x1b4b9]=0;assert(collect(read,r,cache) && r.sources.size()==2);
    m[0x1b4b9]=1;assert(build(read,r) && r.frontier.partial && r.sources.size()==1 && r.sources[0].number==2);
    m[0x1b4b9]=2;assert(!build(read,r) && r.sources.empty());m[0x1b4b9]=0;
    m[base+5]=17;assert(!build(read,r));m[base+5]=1;
    m[data+64+16]=257;assert(!build(read,r));m[data+64+16]=1;
    // Excluded custom definitions may have a non-model operand: never follow it.
    m[data+64+17]=0x04000000;m[data+64+18]=0x980000;
    assert(build(read,r) && !r.sources[0].supported && r.sources[0].words[20]==0);
    m[data+64+17]=0;assert(!build(read,r));
    Source source;std::array<uint32_t,11> words{};
    words[1]=0xc02000;std::array<uint32_t,3> binding={{0xc03000,0x100,0x200}};
    assert(descriptor(words,255,0,256,binding,source) && source.words[6]==0xffff8000);
    assert(!descriptor(words,256,0,256,binding,source));
    // Full El Paso reaches the final front entry before the current section.
    // The lead counter still takes one scene to catch up at that boundary.
    m[0x1b4b5]=base+4;m[0x1b4b6]=1;m[0x1b4b7]=base+8;m[0x1b4b8]=2;
    m[0x1b4bc]=1;m[0x1b4b9]=2;
    assert(collect(read,r,cache) && r.frontier.partial && r.sources.empty());
    m[0x1b4b9]=1;
    assert(collect(read,r,cache) && !r.frontier.partial && r.sources.empty());
    m[0x1b4b9]=3;assert(!collect(read,r,cache) && r.sources.empty());
    m[0x1b4b9]=2;m[base+8]=0;assert(!collect(read,r,cache));
    m[base+8]=0x80000000;m[0x1b4b7]=base+12;assert(!collect(read,r,cache));
}
