// SPDX-License-Identifier: BSD-3-Clause
// Bounded standalone analyzer. Private operands arrive on stdin; no MAME link.
#include "exotica_transform.h"
#include <iostream>
int main()
{
    using namespace cruisn::exotica_transform;
    uint32_t id,previous=0;unsigned count=0;
    while(std::cin>>id)
    {
        uint32_t flags,scale,previous_alpha,alpha,descriptor,alternate_model;
        std::array<uint32_t,3> position,camera;
        std::array<uint32_t,9> view,rotation,alternate;
        if(++count>65536 || id<=previous)return 2;
        previous=id;
        std::cin>>flags>>scale>>previous_alpha>>alpha>>descriptor>>alternate_model;
        for(auto &v:position)std::cin>>v;
        for(auto &v:camera)std::cin>>v;
        for(auto &v:view)std::cin>>v;
        for(auto &v:rotation)std::cin>>v;
        for(auto &v:alternate)std::cin>>v;
        Prepared result;
        if(!std::cin || !prepare(position,camera,view,rotation,alternate,flags,result))return 2;
        const auto command=packet(result,scale,matrix_update(flags,previous_alpha,alpha));
        std::cout<<id<<' '<<result.depth<<' '<<select_model(descriptor,alternate_model,result.depth);
        for(auto v:result.translation)std::cout<<' '<<v;
        for(auto v:result.matrix)std::cout<<' '<<v;
        std::cout<<' '<<command.size();for(auto v:command)std::cout<<' '<<v;
        std::cout<<'\n';
    }
    return std::cin.eof() && count?0:2;
}
