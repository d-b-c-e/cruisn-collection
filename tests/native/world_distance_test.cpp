#include "world_distance.h"
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <vector>
using namespace cruisn::world_distance;
int main(int argc, char **argv)
{
    assert(!valid_far(0) && !valid_far(320000));
    assert(maximum_index(80000)==4999 && maximum_index(100000)==6250 && maximum_index(160000)==10000);
    assert(valid_far(240000) && maximum_index(240000)==15000);
    assert(reciprocal(15001,240000)==0);
    // The immediate and observed backing-RAM range both contain the 3x tail.
    assert(maximum_index(240000)<0x8000 && reciprocal_base+15000<0x20000);
    assert(reciprocal(10000,240000)==reciprocal(10000,160000));
    for (unsigned i=10001;i<=15000;++i)
        assert(reciprocal(i,240000)>0 && reciprocal(i,240000)<=reciprocal(i-1,240000));
    assert(!code_matches(nullptr,0,80000) && !pending_matches(nullptr,0));
    assert(!layout_for_revision(23) && !layout_for_revision(0));
    assert(layout_for_revision(24)->table!=layout_for_revision(25)->table);
    assert(layout_for_revision(24)->pending_pc!=layout_for_revision(25)->pending_pc);
    assert(reciprocal(4999,100000)==0 && reciprocal(6251,100000)==0);
    assert(reciprocal(5000,100000)==0xf851b717 && reciprocal(10000,160000)==0xf751b717);
    for (unsigned i=5001;i<=10000;++i) assert(reciprocal(i,160000)<=reciprocal(i-1,160000));
    assert(projection_pc(0xb4) && projection_pc(0x50e) && !projection_pc(0xb3));
    if (argc>1) {
        const uint32_t revision=argc>2 ? std::strtoul(argv[2],nullptr,10) : 24;
        assert(layout_for_revision(revision));
        std::vector<uint32_t> ram(0x20000);
        std::ifstream input(argv[1],std::ios::binary);
        input.read(reinterpret_cast<char*>(ram.data()),ram.size()*4);
        assert(input.gcount()==0x80000 && code_matches(ram.data(),ram.size(),80000,revision));
        assert(pending_matches(ram.data(),ram.size(),revision));
        assert(!code_matches(ram.data(),ram.size(),80000,revision==24 ? 25 : 24));
        assert(!pending_matches(ram.data(),ram.size(),revision==24 ? 25 : 24));
        const auto original=ram;
        ram[0x40]=240000;
        for (auto const &w:clamps) ram[w.address]=w.value|15000;
        assert(code_matches(ram.data(),ram.size(),240000,revision));
        ram[0xae]=original[0xae];
        assert(!code_matches(ram.data(),ram.size(),240000,revision));
        ram=original;
        for (auto const &site:projection_sites) {
            ram[site.address]^=1;
            assert(!code_matches(ram.data(),ram.size(),80000,revision));
            ram[site.address]^=1;
        }
        const auto *profile=layout_for_revision(revision);
        ram[profile->pending_limit]=12;
        assert(!pending_matches(ram.data(),ram.size(),revision));
        ram=original;
        ram[profile->pending_pc-1]^=1;
        assert(!pending_matches(ram.data(),ram.size(),revision));
    }
}
