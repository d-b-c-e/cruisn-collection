// SPDX-License-Identifier: BSD-3-Clause
#include "phase_timing.h"
#include <cassert>
#include <limits>
using cruisn::PhaseTiming;
int main() {
    PhaseTiming off;assert(off.configure(nullptr));off.add(1,1,PhaseTiming::source,1);
    assert(!off.enabled() && off.size()==0 && !off.configure("1:2"));
    for(auto s:{"","0:1","2:1","1:2001","1","1:",":1","-1:2","1:2x","1:4294967296"," 1:2"}) {
        PhaseTiming p;assert(!p.configure(s) && !p.enabled());
    }
    PhaseTiming p;assert(p.configure("7800:7830"));
    p.add(7799,1,PhaseTiming::source,2);p.add(7831,1,PhaseTiming::source,2);
    assert(p.size()==0 && !p.good(7831));
    p.add(7800,2,PhaseTiming::source,12.5,100);p.add(7830,3,PhaseTiming::active_build,0);
    assert(p.size()==2 && !p.good(7829) && p.good(7830));
    FILE *f=std::tmpfile();assert(f && p.write(f,7830));assert(!std::fclose(f));
    p.add(7801,4,PhaseTiming::source,std::numeric_limits<double>::quiet_NaN());
    assert(!p.good(7830));
    PhaseTiming full;assert(full.configure("1:1"));
    for(size_t i=0;i<PhaseTiming::capacity;++i)full.add(1,1,PhaseTiming::source,0);
    assert(full.good(1));full.add(1,1,PhaseTiming::source,0);assert(!full.good(1));
}
