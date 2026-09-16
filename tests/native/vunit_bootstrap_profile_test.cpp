#include "vunit_bootstrap_profile.h"
#include <cassert>
int main()
{
    // Actual read-tap boundaries captured independently by the Lua observer.
    const char *names[]={"crusnusa","crusnwld24","crusnwld","offroadc"};
    const uint32_t pcs[]={0x81,0x6a,0x6a,0x1bf9};
    const uint32_t addresses[]={0x40,0x61ee,0x658f,0x111f4};
    for(unsigned i=0;i<4;++i){
        auto profile=cruisn::vunit_bootstrap_profile(names[i]);
        assert(profile.pc==pcs[i] && profile.address==addresses[i]);
    }
    assert(!cruisn::vunit_bootstrap_profile(nullptr).address);
    assert(!cruisn::vunit_bootstrap_profile("crusnexo").address);
    assert(!cruisn::vunit_bootstrap_profile("crusnwld23").address);
}
