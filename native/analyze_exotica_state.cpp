// SPDX-License-Identifier: BSD-3-Clause
// Bounded stdin operands. No ROM, MAME linkage or hardware writes.
#include "exotica_state.h"
#include <iostream>
int main()
{
    using namespace cruisn::exotica_state;
    uint32_t id,previous=0;unsigned count=0;
    while(std::cin>>id)
    {
        Operands a;unsigned n=0;
        if(++count>65536 || id<=previous)return 2;
        previous=id;std::cin>>a.flags>>a.palette_setup;
        for(auto &v:a.object)std::cin>>v;
        for(auto &v:a.cache)std::cin>>v;
        for(auto &v:a.constants)std::cin>>v;
        for(auto &v:a.commands)std::cin>>v;
        for(auto &v:a.programs)std::cin>>v;
        for(auto &body:a.bodies)for(auto &v:body)std::cin>>v;
        std::cin>>n;if(!std::cin || n<1 || n>16)return 2;
        a.defaults.resize(n);for(auto &v:a.defaults)std::cin>>v;
        Result r;if(!std::cin || !setup(a,r))return 2;
        std::cout<<id<<' '<<int(r.branch)<<' '<<r.program;
        for(auto v:r.cache)std::cout<<' '<<v;
        std::cout<<' '<<r.packet.size();for(auto v:r.packet)std::cout<<' '<<v;
        std::cout<<'\n';
    }
    return std::cin.eof() && count?0:2;
}
