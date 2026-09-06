// Read packed DMA words and emit adjusted XY floats for offline conformance.
#include <cstdint>
#include "tjunctions.h"
#include <fstream>
#include <iostream>
int main(int argc,char **argv) {
    if (argc!=3) return 2;
    std::ifstream in(argv[1],std::ios::binary|std::ios::ate);
    const auto length=in.tellg();
    if (!in || length<=0 || length%32 || length>32*65535) return 2;
    std::vector<std::array<uint16_t,16>> quads(size_t(length)/32);
    in.seekg(0); in.read(reinterpret_cast<char*>(quads.data()),length);
    if (!in) return 2;
    const auto result=cruisn::align_tjunctions(quads.size(),[&](size_t q){return quads[q].data();});
    std::ofstream out(argv[2],std::ios::binary);
    out.write(reinterpret_cast<const char*>(result.positions.data()),result.positions.size()*32);
    if (!out) return 2;
    std::cout<<result.aligned<<'\n';
}
