#include "zeus_render_policy.h"
#include <cassert>
using namespace cruisn::zeus_policy;
int main()
{
    for(unsigned mask=0;mask<8;++mask)
    {
        const auto r=material(mask,0x82,0x4000,0x20204,64);
        assert(r.blend==bool(mask&4) && r.source_alpha==((mask&4)?256U:64U));
        assert(r.depth_test==bool(mask&2) && r.depth_write==bool(mask&2));
        const auto d=material(mask,0x82,0x1020,0x20202,512);
        assert(!d.depth_test && !d.depth_write && d.source_alpha==256);
        assert(depth(mask,100,50)==((mask&1)?100:150));
        assert(depth(mask,25,50)==((mask&1)?50:75));
        assert(depth(mask,100,-50)==((mask&1)?100:50));
    }
    assert(!material(7,1,0,0x21e0e,256).blend);
    assert(material(7,2,0,0x21e0e,256).blend);
}
