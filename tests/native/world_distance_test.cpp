#include "world_distance.h"
#include <cassert>
#include <fstream>
#include <vector>
using namespace cruisn::world_distance;
int main(int argc, char **argv)
{
    assert(!valid_far(0) && !valid_far(320000));
    assert(maximum_index(80000)==4999 && maximum_index(100000)==6250 && maximum_index(160000)==10000);
    assert(!code_matches(nullptr,0,80000) && !pending_matches(nullptr,0));
    assert(reciprocal(4999,100000)==0 && reciprocal(6251,100000)==0);
    assert(reciprocal(5000,100000)==0xf851b717 && reciprocal(10000,160000)==0xf751b717);
    for (unsigned i=5001;i<=10000;++i) assert(reciprocal(i,160000)<=reciprocal(i-1,160000));
    assert(projection_pc(0xb4) && projection_pc(0x50e) && !projection_pc(0xb3));
    if (argc>1) {
        std::vector<uint32_t> ram(0x20000);
        std::ifstream input(argv[1],std::ios::binary);
        input.read(reinterpret_cast<char*>(ram.data()),ram.size()*4);
        assert(input.gcount()==0x80000 && code_matches(ram.data(),ram.size(),80000));
        assert(pending_matches(ram.data(),ram.size()));
        for (auto const &site:projection_sites) {
            ram[site.address]^=1;
            assert(!code_matches(ram.data(),ram.size(),80000));
            ram[site.address]^=1;
        }
    }
}
