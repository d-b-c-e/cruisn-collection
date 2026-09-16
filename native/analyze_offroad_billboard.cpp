// SPDX-License-Identifier: BSD-3-Clause
// Bounded private captured operands on stdin; no ROM data compiled into binary.
#include "offroad_billboard.h"
#include <iostream>
#include <map>

int main()
{
    uint32_t id,previous=0,count=0;
    while(std::cin>>id) {
        if(id!=previous+1 || ++count>4096)return 2;
        previous=id;
        std::array<uint32_t,22> object;
        std::array<uint32_t,12> view,basis,vertices,matrix,projected;
        uint32_t origin;
        for(auto &w:object)std::cin>>w;
        for(auto &w:view)std::cin>>w;
        for(auto &w:basis)std::cin>>w;
        for(auto &w:vertices)std::cin>>w;
        std::cin>>origin;
        std::map<uint32_t,uint32_t> table;
        for(unsigned i=0;i<4;++i) {
            uint32_t depth,word;if(!(std::cin>>depth>>word) || depth>63679)return 2;
            auto found=table.find(depth);if(found!=table.end() && found->second!=word)return 2;
            table[depth]=word;
        }
        if(!std::cin)return 2;
        if(!cruisn::offroad_billboard::prepare(object,view,basis,matrix))return 3;
        try {
            if(!cruisn::offroad_billboard::project(vertices,matrix,origin,
                [&](uint32_t depth){return table.at(depth);},projected))return 4;
        } catch(const std::out_of_range &) {return 5;}
        std::cout<<id;
        for(auto w:matrix)std::cout<<' '<<w;
        for(auto w:projected)std::cout<<' '<<w;
        std::cout<<'\n';
    }
    return std::cin.eof() && count?0:2;
}
