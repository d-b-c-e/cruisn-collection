#include "exotica_active_capture.h"
#include <cassert>
#include <iostream>
#include <map>
int main() {
    using namespace cruisn::exotica_active;
    std::map<uint32_t,uint32_t> memory;
    auto read=[&](uint32_t a){assert(a<0x40000);return memory[a];};
    auto f=[](int32_t n){return Float::integer(n).store();};
    Parameters p;p.margin=86;p.projection_table=0x20000;p.camera.fill(f(0));
    for(unsigned i=0;i<9;++i)p.view[i]=p.alternate[i]=f(i%4==0);
    p.constants[0]=f(511);p.constants[2]=f(256);p.constants[3]=f(200);p.constants[12]=204800;
    for(unsigned i=0;i<5000;++i)memory[p.projection_table+i]=f(1);
    for(unsigned i=0;i<4;++i)memory[0xbbb5+i]=0x1000+i;
    const uint32_t slot=0x1200;memory[0x1001]=slot;
    memory[slot+15]=0x403;memory[slot+1]=f(-300);memory[slot+2]=f(0);memory[slot+3]=f(1000);memory[slot+21]=10;
    for(unsigned i=0;i<9;++i)memory[slot+5+i]=f(i%4==0);
    auto capture=[&](){Capture c;for(unsigned i=0;i<4;++i)assert(c.capture(0xbbb5+i,read(0xbbb5+i),p,read));return c;};
    auto c=capture();Selections out;
    assert(c.finish(read,{},out) && out.objects==1 && out.candidates==1 && !out.already_submitted);
    assert(out.lists[1].sources.size()==1 && out.lists[1].sources[0].words[15]==3);
    memory[slot+20]=123;memory[slot+31]=456;
    assert(c.finish(read,{},out)); //scratch/neighbor don't belong to the render contract
    assert(c.finish(read,{slot},out) && out.already_submitted==1 && out.lists[1].sources.empty());
    for(unsigned offset:{0u,1u,15u,16u,17u,18u,21u,30u}) {
        auto saved=memory[slot+offset];memory[slot+offset]=saved+1;
        out.objects=999;assert(!c.finish(read,{},out) && out.objects==999);
        memory[slot+offset]=saved;
    }
    memory[p.projection_table+62]=f(2);assert(!c.finish(read,{},out));memory[p.projection_table+62]=f(1);
    memory[0xbbb6]=0x1000;assert(!c.finish(read,{},out));memory[0xbbb6]=0x1001;
    Capture partial;assert(!partial.capture(0xbbb6,0x1001,p,read) && partial.lists()==0);
    assert(partial.capture(0xbbb5,0x1000,p,read));assert(!partial.finish(read,{},out));
    assert(!partial.capture(0xbbb5,0x1000,p,read) && partial.lists()==1);
    assert(partial.capture(0xbbb6,0x1001,p,read));memory[0x1002]=slot;
    assert(!partial.capture(0xbbb7,0x1002,p,read) && partial.lists()==2);memory[0x1002]=0;
    assert(partial.capture(0xbbb7,0x1002,p,read));assert(partial.capture(0xbbb8,0x1003,p,read));
    assert(!partial.capture(0xbbb9,0x1003,p,read) && partial.lists()==4);
    partial.clear();assert(partial.lists()==0 && !partial.finish(read,{},out));
    // Reuse in the NEXT scene takes fresh operands, not a cached RAM-slot identity.
    memory[slot+1]=f(0);auto next=capture();assert(next.finish(read,{},out) && out.candidates==0);
    std::cout<<"PASS owned lists, current membership/field/factor guards, submission exclusion and fresh next-scene slots\n";
}
