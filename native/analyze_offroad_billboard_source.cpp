// SPDX-License-Identifier: BSD-3-Clause
#include "offroad_billboard_source.h"
#include <iostream>
int main()
{
    uint32_t id,count=0,previous=0;
    while(std::cin>>id) {
        if(id<=previous || ++count>32768)return 2;
        previous=id;uint32_t number,ordinal,size,index,bits;
        std::array<uint32_t,11> definition;std::array<uint32_t,3> binding;
        if(!(std::cin>>number>>ordinal>>size>>index>>bits))return 2;
        for(auto &w:definition)std::cin>>w;
        for(auto &w:binding)std::cin>>w;
        if(!std::cin)return 2;
        bool supported;std::array<uint32_t,22> output;
        if(!cruisn::offroad_billboard_source::descriptor(definition,number,ordinal,size,binding,index,bits,supported,output))return 3;
        std::cout<<id<<' '<<unsigned(supported);for(auto w:output)std::cout<<' '<<w;std::cout<<'\n';
    }
    return std::cin.eof() && count?0:2;
}
