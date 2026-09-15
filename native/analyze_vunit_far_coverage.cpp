// SPDX-License-Identifier: BSD-3-Clause
// Offline rows: far, then four x/y/depth triples. Emits 64-byte shader masks.
#include "vunit_far_coverage.h"
#include <iostream>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main()
{
#ifdef _WIN32
    _setmode(_fileno(stdout),_O_BINARY);
#endif
    double far;
    while(std::cin>>far) {
        std::array<cruisn::vunit_far::Point,4> xy;
        std::array<double,4> z;
        for(unsigned i=0;i<4;++i)if(!(std::cin>>xy[i][0]>>xy[i][1]>>z[i]))return 2;
        cruisn::vunit_far::Mask result;
        if(!cruisn::vunit_far::coverage(xy,z,far,result))return 3;
        static_assert(sizeof(result)==64,"coverage mask layout");
        if(!std::cout.write(reinterpret_cast<const char *>(result.data()),sizeof(result)))return 4;
    }
    return std::cin.eof()?0:2;
}
