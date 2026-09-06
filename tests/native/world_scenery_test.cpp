#include "world_scenery.h"
#include <cassert>
#include <vector>
using namespace cruisn::world_scenery;
int main()
{
    assert(classify(0xca57f3,0x80001008,1950)==tree);
    assert(classify(0xca5833,0x1008,1950)==tree);
    assert(classify(0xca5863,0x80001008,818)==tree);
    assert(classify(0xca5896,0x1008,1252)==tree);
    assert(classify(0xca5896,0x1008,818)==other);
    assert(classify(0xca57f3,0x900,1950)==other); // DMA flags aren't object flags
    assert(classify(0xca57f3,0x1008,3000)==other);
    assert(classify(0xcb1a8b,0x1000,26031)==mountain);
    assert(classify(0xcb1831,0x1000,26031)==other); // ground is not a mountain
    assert(admission(tree,80000,1950)==80000 && admission(tree,-10,1950)==80000);
    assert(admission(tree,80001,1950)==156084);
    assert(admission(mountain,80001,26031)==160000);
    assert(admission(other,80001,1950)==80000);
    for (unsigned r=1;r<=2000;++r) assert(admission(tree,80001,r)+2*r<extended_far);
    assert(reciprocal(4999)==0 && reciprocal(10001)==0);
    assert(reciprocal(5000)==0xf851b717 && reciprocal(10000)==0xf751b717);
    for (unsigned i=5001;i<=10000;++i) assert(reciprocal(i)<=reciprocal(i-1));
    std::vector<uint32_t> ram(0x20000);
    assert(!code_matches(ram.data(),ram.size()));
    assert(!code_matches(ram.data(),0x100));
    assert(!projection_pc(0xb4) && !projection_pc(0x50e) && projection_pc(0x21c));
}
