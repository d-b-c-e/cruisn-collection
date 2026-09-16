#include "../../native/vunit_distance_fade.h"
#include "../../native/scenery_c31.h"
#include <cassert>

int main()
{
    using namespace cruisn;
    vunit_fade::Packet p;p.quad.frame=5900;p.quad.pc=0x6a;p.quad.pad=3;
    p.quad.coverage.far_limit=240000;
    const auto fill=[&](std::array<int,4> z) {
        for(unsigned i=0;i<4;++i)p.quad.coverage.words[i]=scenery::Float::integer(z[i]).store();
    };
    std::array<float,4> depths;bool crossing;
    fill({1000,220000,239999,240001});
    assert(vunit_fade::decode(p,depths,crossing) && crossing);
    std::array<double,4> old;
    assert(vunit_far::decode(p.quad.coverage,old));
    for(unsigned i=0;i<4;++i)assert(depths[i]==old[i]);
    p.policy=1;
    assert(vunit_fade::decode(p,depths,crossing));
    p.quad.pad=7;assert(vunit_fade::decode(p,depths,crossing));
    p.policy=0;assert(!vunit_fade::decode(p,depths,crossing));
    p.policy=1;p.quad.pad=3;
    fill({1000,220000,230000,239999});
    assert(vunit_fade::decode(p,depths,crossing) && !crossing);
    assert(!vunit_far::decode(p.quad.coverage,old)); // original codec remains crossing-only
    const auto reject=[&]() {
        depths.fill(123);crossing=true;
        assert(!vunit_fade::decode(p,depths,crossing));
        assert((depths==std::array<float,4>{}) && !crossing);
    };
    p.policy=2;reject();p.policy=0;
    p.quad.pad=1;reject();p.quad.pad=3;
    p.quad.frame=0;reject();p.quad.frame=5900;
    p.quad.coverage.far_limit=160000;reject();p.quad.coverage.far_limit=240000;
    fill({240000,240000,240001,260000});reject();
    for(int invalid:{-1,0,999,480000,1000000}) {
        fill({1000,2000,3000,invalid});reject();
    }
    // Off-Road accepts vertices beyond the sphere admission without clipping.
    p.quad.coverage.far_limit=191040;
    fill({503,141888,167308,191039});
    assert(vunit_fade::decode(p,depths,crossing,vunit_fade::Profile::offroad) && !crossing);
    assert(!vunit_fade::decode(p,depths,crossing)); // explicit profile required
    for(int invalid:{502,191040,240000}) {
        fill({503,1000,141888,invalid});depths.fill(123);crossing=true;
        assert(!vunit_fade::decode(p,depths,crossing,vunit_fade::Profile::offroad));
        assert((depths==std::array<float,4>{}) && !crossing);
    }
    fill({503,141888,167308,191039});
    p.policy=1;assert(!vunit_fade::decode(p,depths,crossing,vunit_fade::Profile::offroad));p.policy=0;
    p.quad.pad=7;assert(!vunit_fade::decode(p,depths,crossing,vunit_fade::Profile::offroad));p.quad.pad=3;
    p.quad.coverage.far_limit=141888;
    assert(!vunit_fade::decode(p,depths,crossing,vunit_fade::Profile::offroad));

}
