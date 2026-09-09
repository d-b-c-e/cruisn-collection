// SPDX-License-Identifier: BSD-3-Clause
// Bounded offline wire format. Uses the same pure codec intended for MAME.
#include "usa_model.h"
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>

int main(int argc,char **argv)
{
    using namespace cruisn::usa_model;
    const bool prepared=argc==2 && std::string(argv[1])=="--prepared";
    if(argc!=2 || (!prepared && std::string(argv[1])!="--captured"))return 2;
    std::array<uint32_t,5080> reciprocals;
    for(auto &word:reciprocals)if(!(std::cin>>word))return 2;
    uint32_t call,compact,direct,count;
    unsigned records=0;
    while(std::cin>>call)
    {
        if(++records>100000 || !(std::cin>>compact>>direct>>count) || compact>1 || direct>1 || count>8192 || count<9)return 2;
        std::vector<uint32_t> words(count);
        for(auto &word:words)if(!(std::cin>>word))return 2;
        Transform transform;transform.compact=bool(compact);
        for(unsigned i=0;i<(compact?4:9);++i)if(!(std::cin>>transform.matrix[i]))return 2;
        for(auto &word:transform.center)if(!(std::cin>>word))return 2;
        if(!(std::cin>>transform.origin_y))return 2;
        if(prepared)
        {
            std::array<uint32_t,32> object;
            std::array<uint32_t,3> camera;
            std::array<uint32_t,9> view,billboard;
            std::array<uint32_t,4> compact_billboard;
            uint32_t mode,enabled,selected;
            for(auto &word:object)if(!(std::cin>>word))return 2;
            for(auto &word:camera)if(!(std::cin>>word))return 2;
            for(auto &word:view)if(!(std::cin>>word))return 2;
            for(auto &word:billboard)if(!(std::cin>>word))return 2;
            for(auto &word:compact_billboard)if(!(std::cin>>word))return 2;
            if(!(std::cin>>mode>>enabled>>selected))return 2;
            Transform computed;
            if(!prepare(object,camera,view,billboard,compact_billboard,bool(compact),transform.origin_y,computed))return 2;
            if(computed.center!=transform.center || computed.matrix!=transform.matrix)
            {std::cerr<<call<<": prepared transform mismatch\n";return 1;}
            if(compact_dispatch(object[14],mode,enabled)!=bool(compact) ||
                select_model(object,Float::load(computed.center[2]).fix())!=selected)
            {std::cerr<<call<<": dispatch/LOD mismatch\n";return 1;}
            transform=computed;
        }
        const unsigned polygons=(words[1]>>16)+1;
        if(polygons>1024 || count!=2+2*((words[1]&255)+1)+5*polygons)return 2;
        std::map<uint32_t,uint32_t> palettes;
        for(unsigned i=0;i<polygons;++i)
        {
            uint32_t value;if(!(std::cin>>value))return 2;
            const auto flags=words[2+2*((words[1]&255)+1)+5*i];
            if(palettes.count(flags) && palettes[flags]!=value)return 2;
            palettes[flags]=value;
        }
        Model model;std::vector<Vertex> vertices;std::vector<Quad> output;
        try
        {
            if(!load([&](uint32_t p){return words.at(p-0xc00000);},0xc00000,model) ||
               !project(model,transform,[&](int32_t i){return reciprocals.at(size_t(i+80));},vertices,Projection::captured) ||
               !quads(model,vertices,bool(direct),[&](uint32_t flags){return palettes.at(flags);},output))
                throw std::runtime_error("USA codec rejected captured record");
        }
        catch(const std::exception &error){std::cerr<<call<<": "<<error.what()<<'\n';return 1;}
        std::cout<<call<<' '<<vertices.size()<<' '<<output.size();
        for(const auto &v:vertices)for(auto word:v)std::cout<<' '<<word;
        for(const auto &q:output)for(auto word:q)std::cout<<' '<<word;
        std::cout<<'\n';
    }
    return records && std::cin.eof()?0:2;
}
