// SPDX-License-Identifier: BSD-3-Clause
#include "usa_future_sections.h"
#include <cassert>
#include <iostream>
#include <map>
int main()
{
    using namespace cruisn;
    const std::array<uint32_t,7> constants={{4263704963U,4118653474U,3979254875U,4088417758U,4178085694U,4258616668U,4788187U}};
    const uint32_t zero=0x80000000,p=0xc10000;
    std::map<uint32_t,uint32_t> memory;
    auto read=[&](uint32_t address){assert(address<0x20000 || (address>=0xc00000 && address<0x1000000));return memory[address];};
    for(unsigned i=0;i<7;++i)memory[0xc8ed+i]=constants[i];
    memory[0x9ea9]=0x1000;memory[0x1003]=5U<<16;memory[0xc00001]=0x2003;
    memory[0x1003]|=1;memory[0x9ea8]=0x2000;memory[0x2005]=0x8003;
    memory[0xa12e]=memory[0xe4a5]=memory[0xe49d]=p;memory[0xe4a4]=0;
    const std::array<uint32_t,12> section={{0x1009,zero,zero,zero,zero,0xc20000,0xc20020,zero,zero,zero,0,0xc20040}};
    for(unsigned i=0;i<12;++i)memory[p+i]=section[i];
    memory[p+12]=UINT32_MAX;
    for(uint32_t block:{0xc20000U,0xc20020U,0xc20040U})
    {
        memory[block+1]=1;memory[block+2]=0xc00002;
        memory[block+6]=zero;memory[block+7]=0xb07;
    }
    usa_future::Result result;
    assert(usa_future::build(read,result) && result.sources.size()==3 && result.end && !result.partial);
    assert(result.sources[0].words[14]==0x10002400 && result.sources[0].words[15]==0x300);
    assert(result.sources[0].words[16]==0x500 && result.sources[0].words[30]==0x1f8);
    assert(result.sources[2].words[30]==0x107 && result.sources[2].words[21]==0);
    memory[0xe4a5]=p+12;memory[0xe4a4]=1;
    assert(usa_future::build(read,result) && result.partial && result.sources.empty());
    memory[0xe49d]=p+12;
    assert(usa_future::build(read,result) && !result.partial && result.sources.empty());
    memory[0xe4a4]=0;
    assert(!usa_future::build(read,result) && result.sources.empty() && result.start==0);
    memory[0xe4a5]=memory[0xe49d]=p;memory[p+5]=0x980040;
    assert(!usa_future::build(read,result) && result.sources.empty());
    memory[p+5]=0xc20000;memory[0xc20001]=4097;
    assert(!usa_future::build(read,result));
    memory[0xc20001]=1;memory[0x9ea9]=0x1ffff;
    assert(!usa_future::build(read,result));
    memory[0x9ea9]=0x1000;memory[0x2005]=0x8004;
    assert(!usa_future::build(read,result));memory[0x2005]=0x8003;
    memory[0x9ea9]=0x1000;memory[0x1003]=0;
    assert(usa_future::build(read,result) && !result.sources[0].resident);
    memory[0xc20002]=0x980040;memory[0xc20007]=0x2000;
    assert(usa_future::build(read,result) && !result.sources[0].supported && !result.sources[0].resident);
    memory[0xe4a5]=memory[0xe49d]=0;
    assert(usa_future::build(read,result) && result.pretrack && result.sources.empty());
    assert(!usa_future::build(read,result,129));
    // Cached placement must refresh current bindings and gate pending uploads.
    memory[0xe4a5]=memory[0xe49d]=p;memory[0xe4a4]=0;
    memory[0xc20002]=0xc00002;memory[0xc20007]=0xb07;
    memory[0x1003]=0x50001;memory[0x62]=0x1000;memory[0xcc3f]=0;
    usa_future::Cache cache;usa_future::Stats stats;
    std::vector<usa_host::Descriptor> objects;
    assert(usa_future::collect(read,cache,objects,stats) && stats.ready==3 && stats.new_sections==1);
    const auto original_id=objects[0].id;
    memory[0x1003]=0x60001;memory[0x2006]=0x8003;
    assert(usa_future::collect(read,cache,objects,stats) && stats.ready==3 && stats.new_sections==0);
    assert(objects[0].words[16]==0x600 && objects[0].id==original_id);
    memory[0xcc3f]=0xcc42;memory[0xcc42]=0;memory[0xcc44]=0x9e0600;memory[0xcc45]=0x80000100;
    assert(usa_future::collect(read,cache,objects,stats) && objects.empty() && stats.deferred==3 && stats.uploads==1);
    memory[0xcc44]=0x9e0700;
    assert(usa_future::collect(read,cache,objects,stats) && objects.size()==3);
    memory[0xcc44]=0xa00000;memory[0xcc45]=1;
    assert(usa_future::collect(read,cache,objects,stats) && objects.empty() && stats.deferred==3);
    memory[0xcc42]=0xcc42;
    assert(!usa_future::collect(read,cache,objects,stats) && objects.empty());
    memory[0xcc3f]=0;memory[0x2006]=0x8004;
    assert(usa_future::collect(read,cache,objects,stats) && objects.empty() && stats.unbound==3);
    memory[0xe4a5]=memory[0xe49d]=0;
    assert(usa_future::collect(read,cache,objects,stats) && stats.pretrack && cache.sections.empty());
    std::cout<<"USA future variable lists, final render fields, bounded frontier and unbound/custom guards PASS\n";
}
