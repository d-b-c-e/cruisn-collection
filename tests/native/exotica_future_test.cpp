#include "exotica_future_sections.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn::exotica_future;
    std::map<uint32_t,uint32_t> m;
    const uint32_t code[][2]={{0xb7e8,0x082e0597},{0xb804,0x08442501},{0xb817,0x152e0597},
        {0xb842,0x084a2501},{0xb859,0x082267c4},{0xb86f,0x14420416},{0xb878,0x08402501},
        {0xb8cb,0x0840041d},{0xbc36,0x08400202},{0xa032,0x0221e67c},{0xa025,0x0221e67d},
        {0x92e8,0x24e02122},{0x92f8,0xc00201c1},{0xb840,0x1420059b},{0xbbaa,0x80000},{0xbbb1,0x4000000}};
    for(const auto &r:code)m[r[0]]=r[1];
    const std::array<uint32_t,7> trig={{4263704963U,4118653474U,3979254875U,4088417758U,4178085694U,4258616668U,4788187U}};
    for(unsigned i=0;i<7;++i)m[0xe991+i]=trig[i];
    m[0x1fbc]=0xa00000;m[0xa00000]=0xa00010;m[0x597]=0xa00017;m[0x590]=256;m[0x598]=30;
    m[0x599]=m[0x59a]=m[0x59c]=0x80000000;m[0x59b]=Float::integer(100).store();
    m[0xe67c]=0x100;m[0xe67d]=0x110;m[0x100]=0xc03000;m[0x110]=0xc03100;
    m[0xc03000]=123;m[0xc03100]=456;m[0xc02001]=10;
    m[0xa00013]=m[0xa00017]=0xc01004;
    for(unsigned i=0;i<4;++i)m[0xa0001b+i]=UINT32_MAX;
    const uint32_t list[]={0x80000000,0x80000000,Float::integer(100).store(),0x80000000,29U<<16,
        0xc02000,5,0,10,0x80000000,0};
    for(unsigned i=0;i<11;++i)m[0xc01000+i]=list[i];
    auto read=[&](uint32_t p){auto it=m.find(p);return it==m.end()?0U:it->second;};
    const auto before=m;Result result;
    assert(build(read,result) && m==before && result.sources.size()==2);
    assert(!result.sources[0].future && result.sources[1].future);
    assert(result.sources[1].words[3]==Float::integer(110).store() && result.sources[1].words[18]==456);
    m[0xc03100]=789;assert(build(read,result) && result.sources[1].words[18]==789);
    assert(build(read,result,true) && !result.sources[1].future);
    m[0x598]=31;assert(!build(read,result) && result.sources.empty());m[0x598]=30;
    m[0xc01005]=0xff980000;assert(build(read,result) && !result.sources[0].supported);
    m[0xc01005]=0x980000;assert(!build(read,result));m[0xc01005]=0xc02000;
    Section section;section.flags=33;section.position={{0x80000000,0x80000000,0x80000000}};
    section.header.fill(0x80000000);section.section_heading=0x01491000;
    section.matrix=cruisn::world_future::yaw(Float::load(0x01491000),trig);
    section.gap=29;section.cursor=100;section.index=2;
    std::array<uint32_t,11> constants{};constants[0]=0x80000;constants[7]=0x4000000;constants[8]=0x8000000;
    std::array<uint32_t,6> definition={{0xc02000,0,0,0,0x80000000,3U*0x4000000|0x8000|0xb05}},model={{0,10,0,0,0,0}};
    Source source;assert(descriptor(definition,model,section,constants,trig,{{17,18}},source));
    assert(source.words[22]==Float::integer(254).store() && source.words[24]==0x2fa && source.words[29]==126);
    assert(source.words[15]==0xc080130 && source.words[16]==0x78080002);
    m[0x597]=0xa0001b;m[0x590]=512;m[0x598]=60;m[0x59b]=Float::integer(200).store();
    assert(build(read,result) && !result.sources.back().future && !build(read,result,true));
    m[0x597]=m[0x590]=m[0x598]=0;assert(build(read,result) && result.pretrack);
    m[0xb7e8]=0;assert(!build(read,result));
}
