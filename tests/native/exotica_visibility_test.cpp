#include "exotica_visibility.h"
#include <cassert>
#include <fstream>
#include <vector>
using namespace cruisn::exotica_visibility;
int main(int argc,char **argv)
{
    std::vector<uint32_t> ram(0x40000);
    if (argc>1) {
        std::ifstream input(argv[1],std::ios::binary);
        input.read(reinterpret_cast<char*>(ram.data()),ram.size()*4);
        assert(input.gcount()==0x100000);
    } else for (auto const &w:guards) ram[w.address]=w.value;
    assert(code_matches(ram.data(),ram.size()));
    for (auto const &w:guards) {
        ram[w.address]^=1;assert(!code_matches(ram.data(),ram.size()));ram[w.address]^=1;
    }
    assert(!code_matches(nullptr,0));
    assert(projection_consumer(0x688c,table_base,4999));
    assert(!projection_consumer(0xc372,table_base,4999)); // short-range helper unchanged
    assert(!projection_consumer(0x688c,table_base+1,4999));
    assert(!projection_consumer(0x688c,table_base,4998));
    assert(reciprocal(5000)==0xf851b717 && reciprocal(12801)==0 && reciprocal(4999)==0);
    // Decode the positive C31 constants independently of the generator.
    auto decode=[](uint32_t v) { return std::ldexp(1.0+(v&0x7fffff)/8388608.0,int8_t(v>>24)); };
    assert(decode(wide_center)==256+88 && decode(wide_upper)==511+2*88);
    uint32_t object=0x20000;
    auto read=[&](int32_t depth,int32_t radius,uint32_t sum) {
        ram[object+0x14]=uint32_t(depth);ram[object+0x15]=uint32_t(radius);
        return read_sample(ram.data(),ram.size(),object,sum);
    };
    assert(extends(read(160000,1000,161000)));
    assert(read(160000,1000,161000).index==10000);
    assert(!extends(read(79999,1000,80999)));
    assert(!extends(read(205000,1,205001))); // delay-slot reciprocal follows far rejection
    assert(!read(160000,-1,159999).valid);
    assert(!read(160000,1000,161001).valid);
    assert(!read(-1000,100,0).valid);
    assert(read(-1000,1100,100).valid && !extends(read(-1000,1100,100)));
    assert(!read_sample(ram.data(),ram.size(),0xffffffff,0).valid);
    assert(!read_sample(ram.data(),ram.size(),0x3ffeb,0).valid);
}
