#include "exotica_source_cache.h"
#include <cassert>
#include <iostream>
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
    CachedSources cache;Result full,cached;
    auto check=[&](uint64_t owner,bool partial=false){
        const bool ok=build(read,full,partial);
        assert(cache.build(read,owner,cached,partial)==ok);
        assert(equal_sources(full,cached));return ok;
    };
    assert(check(1));assert(check(1));assert(cache.hits==1 && cache.misses==1);
    const auto saved=m;const auto baseline=full;
    for(const auto &section:baseline.sections)for(unsigned partial=0;partial<2;++partial)
    {
        m[0x590]=section.index*256;m[0x597]=section.entry;m[0x598]=section.cursor;m[0x59c]=section.heading;
        for(unsigned i=0;i<3;++i)m[0x599+i]=section.position[i];
        assert(check(1,partial));m[0x599]^=1;assert(!check(1,partial));m[0x599]^=1;
    }
    m=saved;m[0x110]=0xc03101;m[0xc03101]=789;
    assert(check(1) && cached.sources[1].words[18]==789);
    assert(!equal_sources(baseline,cached));
    m=saved;assert(check(1));m[0xb7e8]^=1;assert(!check(1));
    m=saved;assert(check(1));
    // Mutable ROM requires a new owner or explicit invalidation. The contract
    // deliberately cannot infer external writes that bypass the caller.
    m[0xc03100]=321;assert(check(2) && cached.sources[1].words[18]==321);
    m[0xc03100]=654;cache.invalidate();assert(check(2) && cached.sources[1].words[18]==654);
    m[0x597]=0xa0001b;m[0x590]=512;m[0x598]=60;m[0x59b]=Float::integer(200).store();
    assert(check(2));assert(!check(2,true));
    m[0x597]=m[0x590]=m[0x598]=0;assert(check(2) && cached.pretrack);
    m[0xb7e8]=0;assert(!check(2));
    m=saved;assert(check(2));assert(!cache.build(read,0,cached) && cached.sources.empty());
    std::cout<<"PASS cached source dependencies, frontiers, terminal, ownership and reset\n";
}
