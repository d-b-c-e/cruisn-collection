// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_waiting_handover.h"
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
    for(unsigned i=0;i<4;++i) {
        const uint32_t address=0x1200+i*31;
        exotica_future::Source source;source.supported=true;source.entry=0xa02000;
        source.source=0xa03000+i*6;source.index=i;
        for(unsigned k=0;k<31;++k)source.words[k]=memory[address+k]=100+i*50+k;
        source.words[15]=memory[address+15]=0x04000530;
        sources.push_back(source);uint64_t generation=0;assert(registry.allocate(address,generation));
        scenery_lifetimes::Key key;key.realm=realm;key.section=source.entry;key.source=source.source;
        scenery_lifetimes::Handle handle;assert(registry.bind(address,key,handle));handles.push_back(handle);
    }
    auto read=[&](uint32_t address){assert(memory.count(address));return memory.at(address);};
    exotica_waiting::Pending pending;exotica_waiting::Completion result;
    result.captured=999;
    assert(!pending.complete(registry,9,result) && result.captured==999);
    assert(!pending.capture(sources,realm,registry,0,read));
    assert(pending.capture(sources,realm,registry,9,read));
    assert(pending.selection().items.size()==4);
    assert(!pending.capture(sources,realm,registry,9,read));
    // Binding/submission order needs the observation watermark, even when the
    // pool sequence itself has not advanced. Failure keeps output/pending intact.
    assert(!pending.complete(registry,8,result) && result.captured==999 && pending.pending());
    bool first=false,unknown=false;uint64_t generation=0;
    assert(registry.submitted(handles[1],20,first) && first);
    assert(registry.release(handles[2].slot,unknown) && !unknown);
    assert(registry.allocate(handles[2].slot,generation));
    scenery_lifetimes::Handle replacement;
    assert(registry.bind(handles[2].slot,handles[2].key,replacement));
    assert(replacement.generation!=handles[2].generation);
    memory[handles[0].slot+20]=9876; // Later scratch/fade must not rewrite the captured proposal.
    assert(pending.complete(registry,13,result) && !pending.pending());
    assert(result.captured==4 && result.submitted==1 && result.retired==1 && result.items.size()==2);
    assert(result.items[0].owner.slot==handles[0].slot && result.items[1].owner.slot==handles[3].slot);
    assert(result.items[0].source.words[20]==sources[0].words[20]);
    assert(!result.items[0].source.future && result.items[0].source.words[31]==0);
    assert(result.items[0].source.words[15]==0x04000130); // No host opacity override.
    assert(!pending.complete(registry,13,result));
    assert(pending.capture(sources,realm,registry,13,read));
    assert(pending.selection().items.size()==3); // Derive afresh; replacement has its own generation.
    assert(registry.reset(layout));result.captured=888;
    assert(!pending.complete(registry,14,result) && result.captured==888 && pending.pending());
    pending.cancel();assert(!pending.pending() && pending.selection().items.empty());
    assert(!pending.capture(sources,0,registry,14,read) && !pending.pending());
    assert(pending.capture(sources,realm,registry,14,read));
    assert(pending.complete(registry,14,result) && result.captured==0 && result.items.empty());
    std::cout<<"PASS derived waiting cohort, submission retirement, slot reuse, immutable DTOs, order, reset and transactional errors\n";
}
