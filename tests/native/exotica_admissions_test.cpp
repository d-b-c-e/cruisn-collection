// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_admissions.h"
#include <cassert>
#include <iostream>
using namespace cruisn;
using namespace exotica_admissions;
int main() {
    scenery_lifetimes::Registry registry;scenery_lifetimes::Layout layout;
    layout.first=0x1000;layout.last=0x40000-31;layout.max_tracked=4096;
    assert(registry.start(layout,true));Ledger ledger;assert(ledger.reset(1));
    Key k;k.realm=1;k.section=2;k.source=3;Draw draw;draw.key=k;draw.quads=8;
    Entry output;output.first_sequence=999;
    assert(ledger.admit(1,100,{draw},registry) && ledger.size()==1);
    uint64_t generation=0;Handle h;bool unknown=false;
    assert(registry.allocate(0x1000,generation) && registry.bind(0x1000,k,h));
    assert(ledger.qualify(h,output)==Status::invalid && output.first_sequence==999);
    assert(!ledger.admit(2,101,{draw},registry)); // missed binding is not repaired
    assert(ledger.bind(h)==Status::matched && ledger.bind(h)==Status::invalid);
    assert(ledger.qualify(h,output)==Status::matched && output.first_sequence==1);
    const Entry queued=output; // commit owns this proof even if source is retired
    auto stale=h;++stale.generation;
    assert(ledger.release(stale)==Status::invalid && ledger.size()==1);
    assert(ledger.admit(2,101,{draw},registry));
    assert(!ledger.admit(2,102,{draw},registry));
    assert(!ledger.admit(3,100,{draw},registry));
    auto bad=draw;bad.quads=0;
    assert(!ledger.admit(3,102,{draw,bad},registry));
    assert(!ledger.admit(3,102,{draw,draw},registry));
    assert(ledger.qualify(h,output)==Status::matched && output.last_sequence==2);
    assert(registry.release(h.slot,unknown) && ledger.release(h)==Status::matched);
    assert(ledger.qualify(h,output)==Status::unadmitted && queued.first_sequence==1);
    Handle replacement;
    assert(registry.allocate(h.slot,generation) && registry.bind(h.slot,k,replacement));
    assert(ledger.bind(replacement)==Status::unadmitted); // same key/slot is a new generation
    assert(ledger.qualify(replacement,output)==Status::unadmitted);
    assert(ledger.admit(3,103,{draw},registry)); // explicit new draw qualifies new occupant
    assert(ledger.qualify(h,output)==Status::invalid);
    assert(ledger.qualify(replacement,output)==Status::matched && output.first_sequence==3);
    assert(registry.reset(layout));assert(!ledger.admit(4,104,{draw},registry));
    assert(ledger.reset(2) && !ledger.reset(2) && ledger.size()==0);
    assert(ledger.qualify(replacement,output)==Status::invalid);
    assert(ledger.admit(1,105,{},registry) && ledger.size()==0);
    assert(ledger.admit(2,105,{draw},registry));
    std::cout<<"PASS future-to-owner admission, reuse, retirement, reset and transactional rejection\n";
}
