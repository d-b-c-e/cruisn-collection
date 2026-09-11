// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_waiting.h"
#include <cassert>
#include <iostream>
#include <map>

int main() {
    using namespace cruisn;
    scenery_lifetimes::Registry registry;
    scenery_lifetimes::Layout layout;layout.first=0x1000;layout.last=0x40000-31;layout.max_tracked=4096;
    assert(registry.start(layout));
    const uint64_t realm=(uint64_t(1)<<32)|0xa01000;
    std::map<uint32_t,uint32_t> memory;memory[0x75]=0;
    std::vector<exotica_future::Source> sources;
    std::vector<scenery_lifetimes::Handle> handles;
    for(unsigned index=0;index<3;++index) {
        const uint32_t address=0x1200+index*31;
        exotica_future::Source s;s.supported=true;s.entry=0xa02000;s.source=0xa03000+index*6;s.index=index;
        for(unsigned k=0;k<31;++k)s.words[k]=memory[address+k]=1000+index*50+k;
        s.words[15]=memory[address+15]=0x04000530;
        sources.push_back(s);
        uint64_t generation=0;assert(registry.allocate(address,generation));
        scenery_lifetimes::Key key;key.realm=realm;key.section=s.entry;key.source=s.source;
        scenery_lifetimes::Handle handle;assert(registry.bind(address,key,handle));handles.push_back(handle);
    }
    auto read=[&](uint32_t address) {assert(memory.count(address));return memory.at(address);};
    exotica_waiting::Result result;
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.size()==3);
    for(unsigned i=0;i<3;++i) {
        assert(result.items[i].owner.generation==handles[i].generation && !result.items[i].source.future);
        assert(result.items[i].source.words[31]==0 && result.items[i].source.words[15]==0x04000130);
    }
    // Neighbor offset31 aliases another object: its value must not enter the DTO.
    assert(memory[handles[0].slot+31]!=0 && result.items[0].source.words[31]==0);
    bool first=false;assert(registry.submitted(handles[1],20,first) && first);
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.size()==2 && result.submitted==1);
    assert(result.items[0].source.source==sources[0].source && result.items[1].source.source==sources[2].source);
    bool unknown=false;assert(registry.release(handles[0].slot,unknown) && !unknown);
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.size()==1 && result.unowned==1);
    uint64_t generation=0;assert(registry.allocate(handles[0].slot,generation));
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.size()==1); // Reused, unbound slot cannot borrow old identity.
    assert(exotica_waiting::select(sources,realm+1,registry,read,result) && result.items.empty() && result.unowned==3);
    sources[2].future=true;
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.empty() && result.bound_future==1 && !result.bound_future_submitted);
    sources[1].future=true;
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.bound_future_submitted==1);
    sources[1].future=false;sources[2].future=false;
    // Every immutable operand is checked independently; mutable scratch/fade are current.
    for(unsigned i=0;i<31;++i) {
        if(!exotica_waiting::immutable(i))continue;
        const auto address=handles[2].slot+i;const auto saved=memory[address];memory[address]=saved+1;
        result.historical=999;
        assert(!exotica_waiting::select(sources,realm,registry,read,result) && result.historical==999);
        memory[address]=saved;
    }
    memory[handles[2].slot+20]=789;memory[0x75]=0x100;
    assert(exotica_waiting::select(sources,realm,registry,read,result));
    assert(result.items[0].source.words[20]==789 && result.items[0].source.words[15]==0x04000530);
    sources.push_back(sources.back());assert(!exotica_waiting::select(sources,realm,registry,read,result));sources.pop_back();
    sources[2].source=0xfffffc;assert(!exotica_waiting::select(sources,realm,registry,read,result));sources[2].source=0xa0300c;
    assert(!exotica_waiting::select(sources,0,registry,read,result));
    assert(registry.reset(layout));
    assert(exotica_waiting::select(sources,realm,registry,read,result) && result.items.empty());
    // An address accepted by the generic registry can still be in the device
    // command ring. This adapter rejects it before reading object operands.
    scenery_lifetimes::Registry ring;
    assert(ring.start(layout));assert(ring.allocate(0x30000,generation));
    scenery_lifetimes::Key ring_key;ring_key.realm=realm;
    ring_key.section=sources[0].entry;ring_key.source=sources[0].source;
    scenery_lifetimes::Handle ring_handle;assert(ring.bind(0x30000,ring_key,ring_handle));
    result.historical=999;
    assert(!exotica_waiting::select(sources,realm,ring,read,result) && result.historical==999);
    std::vector<exotica_future::Source> oversized(32769);
    assert(!exotica_waiting::select(oversized,realm,registry,read,result));
    assert(!exotica_waiting::select(sources,(uint64_t(4)<<32)|0xa01000,registry,read,result));
    assert(!exotica_waiting::select(sources,(uint64_t(1)<<32)|0x900000,registry,read,result));
    assert(exotica_waiting::slot(0x2ffe1) && exotica_waiting::slot(0x32000) && exotica_waiting::slot(0x3ffe1));
    assert(!exotica_waiting::slot(0x2ffe2) && !exotica_waiting::slot(0x31fff) && !exotica_waiting::slot(0x3ffe2));
    std::cout<<"PASS waiting eligibility, first submission, reset/reuse/realm, immutable fields, ordering and padding isolation\n";
}
