// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_active.h"
#include <cassert>
#include <iostream>
#include <map>
int main()
{
    using namespace cruisn::exotica_active;
    auto f=[](int32_t n){return Float::integer(n).store();};
    std::map<uint32_t,uint32_t> memory;size_t reads=0;
    auto read=[&](uint32_t a){assert(a<0x40000);++reads;return memory[a];};
    memory[0x1000]=0x1200;memory[0x1200]=0x1300;memory[0x1201]=123;
    memory[0x1200+31]=456; //neighbor word is not part of the captured operands
    std::vector<Source> sources;
    assert(read_list(0xbbb6,0x1000,read,sources) && sources.size()==2 && reads==63);
    assert(sources[0].words[1]==123 && sources[0].words[31]==0);
    memory[0x1300]=0x1200;
    assert(!read_list(0xbbb6,0x1000,read,sources) && sources.empty());
    memory[0x1300]=0x1000;assert(!read_list(0xbbb6,0x1000,read,sources));
    memory[0x1300]=0x3ffe2;assert(!read_list(0xbbb6,0x1000,read,sources));
    assert(!read_list(0xbbb9,0x1000,read,sources));
    assert(!read_list(0xbbb6,0x40000,read,sources));
    memory[0x1000]=0;assert(read_list(0xbbb5,0x1000,read,sources) && sources.empty());
    Source source;source.entry=0xbbb6;source.source=0x1200;source.words[15]=3;
    source.words[1]=f(-300);source.words[2]=f(0);source.words[3]=f(1000);source.words[21]=10;
    Parameters p;p.margin=86;p.projection_table=0x2000;p.camera.fill(f(0));
    for(unsigned i=0;i<9;++i)p.view[i]=p.alternate[i]=source.words[5+i]=f(i%4==0);
    p.constants[0]=f(511);p.constants[2]=f(256);p.constants[3]=f(200);p.constants[12]=204800;
    for(unsigned i=0;i<5000;++i)memory[p.projection_table+i]=f(1);
    Decision d;
    auto check=[&](Reason r,Reason wide){assert(classify(source,p,read,d));assert(d.stock==r && d.wide==wide);};
    check(Reason::left,Reason::admitted);assert(d.margin_candidate && d.depth==1000 && d.index==62);
    p.margin=0;check(Reason::left,Reason::left);assert(!d.margin_candidate);p.margin=86;
    source.words[1]=f(300);check(Reason::right,Reason::admitted);
    source.words[1]=f(0);check(Reason::admitted,Reason::admitted);assert(!d.margin_candidate);
    source.words[2]=f(-211);check(Reason::vertical_low,Reason::vertical_low);
    source.words[2]=f(211);check(Reason::vertical_high,Reason::vertical_high);source.words[2]=f(0);
    source.words[3]=f(204791);check(Reason::distance,Reason::distance);
    source.words[3]=f(-11);check(Reason::distance,Reason::distance);
    source.words[3]=f(-5);check(Reason::admitted,Reason::admitted);assert(d.depth==-5 && d.index==0);
    source.words[3]=f(1000);source.words[21]=UINT32_MAX;assert(!classify(source,p,read,d));source.words[21]=10;
    source.words[15]=0x83;check(Reason::unsupported,Reason::unsupported);
    source.words[15]=1;check(Reason::unsupported,Reason::unsupported);source.words[15]=3;
    p.margin=257;assert(!classify(source,p,read,d));p.margin=86;
    p.constants[0]=f(512);assert(!classify(source,p,read,d));p.constants[0]=f(511);
    memory[p.projection_table+62]=f(0);assert(!classify(source,p,read,d));memory[p.projection_table+62]=f(1);
    source.words[31]=1;assert(!classify(source,p,read,d));source.words[31]=0;
    source.entry=0xa00000;assert(!classify(source,p,read,d));source.entry=0xbbb6;
    source.words[15]=0x403;check(Reason::admitted,Reason::admitted);assert(d.flags==3);
    p.mode=0x100;check(Reason::admitted,Reason::admitted);assert(d.flags==0x403);
    std::cout<<"PASS current object ownership, bounded lists, exact sphere planes and explicit unsupported states\n";
}
