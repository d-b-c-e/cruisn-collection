#include "usa_distance.h"
#include <cassert>
#include <fstream>
#include <vector>
using namespace cruisn::usa_distance;
int main(int argc,char **argv)
{
    assert(!code_matches(nullptr,0,80000) && !residency_matches(nullptr,0));
    assert(admission_limit(80000)==75000 && admission_limit(160000)==150000);
    assert(maximum_index(240000)==15000 && reciprocal_base+15000<0x20000);
    assert(reciprocal(5000,160000)==0xf851b717);
    assert(projection_base(0x27d,0xc700,0xc700,0,reciprocal_base));
    assert(!projection_base(0x27d,0xc700,0xc700,0,0));
    assert(!projection_base(0x27d,0xc700,reciprocal_base,0,reciprocal_base));
    assert(projection_base(0x15e,0xc700,reciprocal_base,0,0));
    assert(!projection_base(0x15e,0xc700,0xc700,0,0));
    assert(projection_base(0xd6,0xc700,0,0xc700,0));
    assert(!projection_base(0xd5,0xc700,0,0xc700,0));
    // Include the unclamped attached-object lookup; do not widen the separate
    // screen-extremum helper's intentional index >=4999 rejection.
    assert(projection_pc(0xa729) && !projection_pc(0x8242));
    std::vector<uint32_t> ram(0x20000);
    if (argc>1) {
        std::ifstream input(argv[1],std::ios::binary);
        input.read(reinterpret_cast<char*>(ram.data()),ram.size()*4);
        assert(input.gcount()==0x80000);
    } else {
        ram[0x55]=80000;ram[0x52]=reciprocal_base;ram[0xcb]=0x04a30055;
        ram[0xa727]=0x082a0052;ram[0xa725]=0x0852041c;ram[0xa726]=0x03f2fffc;
        ram[0x727d]=75000;ram[0x727e]=80000;
        for (auto const &w:clamps) ram[w.address]=w.value|4999;
        for (auto const &w:projection_sites) ram[w.address]=w.value;
        for (auto const &w:residency_sites) ram[w.address]=w.value;
    }
    assert(code_matches(ram.data(),ram.size(),80000));
    assert(residency_matches(ram.data(),ram.size()));
    for (auto const &w:projection_sites) {
        ram[w.address]^=1;assert(!code_matches(ram.data(),ram.size(),80000));ram[w.address]^=1;
    }
    for (auto const &w:residency_sites) {
        ram[w.address]^=1;assert(!residency_matches(ram.data(),ram.size()));ram[w.address]^=1;
    }
    ram[0x55]=160000;
    assert(!code_matches(ram.data(),ram.size(),160000));
    for (auto const &w:clamps) ram[w.address]=w.value|10000;
    assert(code_matches(ram.data(),ram.size(),160000));
    ram[0x277]=0x04e01387;
    assert(!code_matches(ram.data(),ram.size(),160000));
}
