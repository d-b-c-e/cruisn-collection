// SPDX-License-Identifier: BSD-3-Clause
// Bounded private captured operands on stdin; no ROM data compiled into binary.
#include "offroad_billboard.h"
#include <iostream>
#include <map>
#include <string>

int main(int argc,char **argv)
{
    const bool quads=argc==2 && std::string(argv[1])=="--quad";
    if(argc!=1 && !quads)return 2;
    uint32_t id,previous=0,count=0;
    while(std::cin>>id) {
        if(id!=previous+1 || ++count>4096)return 2;
        previous=id;
        std::array<uint32_t,22> object;
        std::array<uint32_t,12> view,basis,vertices,matrix,projected;
        uint32_t origin;
        for(auto &w:object)std::cin>>w;
        if(quads) {
            std::array<uint32_t,6> polygon;std::array<uint16_t,16> output;
            uint32_t palette,extra;
            for(auto &w:polygon)std::cin>>w;
            for(auto &w:projected)std::cin>>w;
            if(!(std::cin>>palette>>extra))return 2;
            if(!cruisn::offroad_billboard::quad(object,polygon,projected,palette,extra,output))return 6;
            std::cout<<id;for(auto w:output)std::cout<<' '<<w;std::cout<<'\n';continue;
        }
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
