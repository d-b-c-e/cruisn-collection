// license:BSD-3-Clause
#include "zeus_sky_repeat.h"
#include <iostream>
#include <iomanip>
#include <cstring>
int main()
{
    unsigned n,margin;
    while (std::cin>>n>>margin) {
        if (n>64) return 2;
        std::vector<cruisn::zeus_sky_tile> tiles(n);
        for (auto &tile:tiles) {
            for (auto &w:tile.state) if (!(std::cin>>w)) return 2;
            for (auto &v:tile.v) for (auto &f:v) { uint32_t w; if (!(std::cin>>w)) return 2; std::memcpy(&f,&w,4); }
        }
        auto p=cruisn::zeus_sky_repeat(tiles,margin);
        std::cout<<p.accepted<<' '<<std::setprecision(10)<<p.period<<' '<<p.comparisons<<' '<<p.copies.size();
        for (auto c:p.copies) { uint32_t bits;std::memcpy(&bits,&c.shift,4);std::cout<<' '<<c.index<<' '<<bits; }
        std::cout<<'\n';
    }
}
