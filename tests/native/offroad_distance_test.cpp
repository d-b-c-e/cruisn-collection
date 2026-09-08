#include "offroad_distance.h"
#include <cassert>
#include <fstream>
#include <vector>
using namespace cruisn::offroad_distance;
int main(int argc,char **argv)
{
    assert(!code_matches(nullptr,0));
    assert(!valid_multiplier(0) && !valid_multiplier(4));
    assert(maximum_index(1)==63679 && maximum_index(3)==191039);
    assert(far_word(1)==0x0f38c000 && clip_word(1)==0x0f78c000);
    assert(far_word(2)==0x1038c000 && clip_word(2)==0x1078c000);
    assert(far_word(3)==0x110a9000 && clip_word(3)==0x113a9000);
    assert(!reciprocal(-4097) && !reciprocal(191040));
    assert(reciprocal(503)==0 && reciprocal(504)!=0); // C31 1.0 is zero bits.
    // Original ROM entries that distinguish decimal ties-to-even from binary rounding.
    assert(reciprocal(20479)==0xfa49999c && reciprocal(61439)==0xf9066661);
    assert(reciprocal(-4096)==0x03220000 && reciprocal(63679)==0xf901ac1d);
    assert(indexed_read(table_base-1,table_base,uint32_t(-1)));
    assert(indexed_read(table_base+70000,table_base,70000));
    assert(!indexed_read(table_base+70000,0,70000));
    assert(!indexed_read(table_base+70000,table_base,69999));
    assert(!projection_site(0x1ea8)); // Resource read: stale AR0 is insufficient.
    assert(far_pc(0x1c36) && !far_pc(0x1c35));
    assert(clip_pc(0x1df9) && clip_pc(0x1e9e) && !clip_pc(0x1824));
    std::vector<uint32_t> ram(0x20000);
    if (argc>1) {
        std::ifstream input(argv[1],std::ios::binary);
        input.read(reinterpret_cast<char*>(ram.data()),ram.size()*4);
        assert(input.gcount()==0x80000);
    } else {
        for (auto const &w:guards) ram[w.address]=w.value;
        for (auto const &w:projection_sites) ram[w.address]=w.value;
        for (auto const &w:ceiling_sites) ram[w.address]=w.value;
    }
    assert(code_matches(ram.data(),ram.size()));
    for (auto const &w:guards) {
        ram[w.address]^=1;assert(!code_matches(ram.data(),ram.size()));ram[w.address]^=1;
    }
    for (auto const &w:projection_sites) {
        assert(projection_site(w.address+1)==&w);
        ram[w.address]^=1;assert(!code_matches(ram.data(),ram.size()));ram[w.address]^=1;
    }
    for (auto const &w:ceiling_sites) {
        assert(ceiling_pc(w.address+1));
        ram[w.address]^=1;assert(!code_matches(ram.data(),ram.size()));ram[w.address]^=1;
    }
    if (argc>2) {
        std::ofstream out(argv[2],std::ios::binary);
        for (int32_t i=minimum_index;i<=int32_t(maximum_index(3));++i) {
            uint32_t w=reciprocal(i);out.write(reinterpret_cast<char*>(&w),4);
        }
        assert(out.good());
    }
}
