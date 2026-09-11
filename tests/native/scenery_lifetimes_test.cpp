// SPDX-License-Identifier: BSD-3-Clause
#include "scenery_lifetimes.h"
#include <cassert>
#include <iostream>
using namespace cruisn::scenery_lifetimes;
static Key key(uint64_t realm,uint32_t section,uint32_t source) {
    Key k;k.realm=realm;k.section=section;k.source=source;return k;
}
int main() {
    Layout l;l.first=100;l.last=223;l.max_tracked=4;
    Registry r;uint64_t generation=999;bool first=false,unknown=false;Handle h,old;State state;
    assert(!r.allocate(100,generation) && generation==999);
    assert(r.start(l) && r.sequence()==0 && r.epoch()==1 && !r.start(l));
    assert(!r.allocate(99,generation) && !r.allocate(0,generation) && !r.allocate(224,generation));
    assert(r.release(100,unknown) && unknown && r.sequence()==1);
    assert(!r.release(100,unknown) && r.sequence()==1);
    assert(r.allocate(100,generation) && generation==2);
    assert(!r.allocate(100,generation) && r.sequence()==2);
    const Key source=key(1,50,60);
    assert(!r.bind(131,source,h) && !r.bind(100,Key(),h));
    assert(r.bind(100,source,h) && r.bound_sources()==1);old=h;
    assert(r.lookup(source,h) && r.inspect(h,state) && !state.last_submission);
    assert(r.submitted(h,10,first) && first);
    assert(r.submitted(h,10,first) && !first && r.submitted(h,11,first) && !first);
    assert(!r.submitted(h,9,first) && !r.submitted(h,0,first));
    assert(r.allocate(131,generation));
    assert(!r.bind(131,source,h) && !r.bind(100,key(2,50,60),h));
    assert(r.bind(131,key(2,50,60),h)); // same source in a different track/bank realm
    assert(!r.inspect(Handle(),state));
    Handle wrong=old;wrong.key.realm=2;assert(!r.inspect(wrong,state));
    wrong=old;wrong.generation++;assert(!r.inspect(wrong,state));
    assert(r.release(100,unknown) && !unknown && !r.inspect(old,state));
    assert(r.allocate(100,generation) && generation==5 && r.bind(100,source,h));
    assert(!r.submitted(old,12,first) && r.submitted(h,12,first) && first);
    old=h;const auto sequence=r.sequence();Layout bad=l;bad.max_tracked=4097;
    assert(!r.reset(bad) && r.sequence()==sequence && r.inspect(old,state));
    assert(r.reset(l) && r.sequence()==sequence+1 && r.epoch()==2 && r.bound_sources()==0);
    assert(!r.lookup(source,h) && !r.inspect(old,state) && !r.release(100,unknown));
    for(unsigned i=0;i<10000;++i) {
        assert(r.allocate(100,generation) && r.bind(100,source,h));
        assert(!r.inspect(old,state) && r.submitted(h,1,first) && first);
        old=h;assert(r.release(100,unknown) && !unknown);
    }
    Layout reversed;l.first=1;l.last=10000;l.max_tracked=2;
    reversed.first=0xfffffff0;reversed.last=100;reversed.max_tracked=2;
    Registry fresh;assert(!fresh.start(reversed));assert(fresh.start(l,false));
    assert(!fresh.release(1,unknown) && fresh.allocate(4096,generation));
    assert(fresh.allocate(537,generation)); // adopted external slot, no stride requirement
    assert(!fresh.allocate(600,generation)); // bounded distinct address history
    assert(fresh.release(537,unknown) && !fresh.allocate(600,generation));
    assert(fresh.allocate(537,generation));
    std::cout<<"PASS stale generations, source realms, reset epochs, partial observation, bounds and 10000 slot reuses\n";
}
