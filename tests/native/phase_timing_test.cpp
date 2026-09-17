// SPDX-License-Identifier: BSD-3-Clause
#include "phase_timing.h"
#include <cassert>
#include <limits>
#include <string>
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
    PhaseTiming events;assert(events.configure("1:3"));
    events.accumulate(1,0,PhaseTiming::lifetime_install,2);
    events.add(1,1,PhaseTiming::source,5);
    events.accumulate(1,0,PhaseTiming::lifetime_install,3);
    events.accumulate(1,0,PhaseTiming::lifetime_complete,4);
    events.accumulate(2,0,PhaseTiming::lifetime_install,6);
    assert(events.size()==4 && events.good(3));
    f=std::tmpfile();assert(f && events.write(f,3));std::rewind(f);
    char line[200];assert(std::fgets(line,sizeof(line),f));assert(std::fgets(line,sizeof(line),f));
    assert(std::string(line)=="1,0,lifetime_install,5.000,2\n");std::fclose(f);
    events.accumulate(3,1,PhaseTiming::source,2);assert(!events.good(3));
}
