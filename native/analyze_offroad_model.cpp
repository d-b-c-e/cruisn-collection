// SPDX-License-Identifier: BSD-3-Clause
// Bounded, ROM-free executable; private captures are supplied through stdin.
#include "offroad_model.h"
#include "offroad_transform.h"
#include <iostream>
#include <map>
#include <string>
int main(int argc,char **argv)
{
    using namespace cruisn::offroad_model;
    const bool prepared=argc==2 && std::string(argv[1])=="--prepared";
    if(argc!=1 && !prepared)return 2;
    std::vector<uint32_t> reciprocals(67776);
    for(auto &v:reciprocals)if(!(std::cin>>v))return 2;
    std::vector<uint32_t> trigonometry;
    if(prepared)
    {
        for(uint32_t expected:{0x1ffffU,0x3fffU,0xef000040U,0xc23e97U})
        {uint32_t value;if(!(std::cin>>value) || value!=expected)return 2;}
        trigonometry.resize(16386);
        for(auto &v:trigonometry)if(!(std::cin>>v))return 2;
    }
    uint32_t id,previous=0;unsigned records=0;
    while(std::cin>>id)
    {
        uint32_t lod,nv,np,origin,path,extra,palette_base,texture_base;
        if(!(std::cin>>lod>>nv>>np>>origin>>path>>extra>>palette_base>>texture_base))return 2;
        if(++records>20000 || id<=previous || !nv || nv>512 || !np || np>1024 || !rom_span(lod,5))return 2;
        previous=id;
        std::array<uint32_t,5> descriptor;
        std::array<uint32_t,12> matrix;
        for(auto &v:descriptor)std::cin>>v;
        for(auto &v:matrix)std::cin>>v;
        if(descriptor[0]!=nv-1 || descriptor[3]!=np-1 ||
            !rom_span(descriptor[1],3*nv) || !rom_span(descriptor[4],6*np))return 2;
        std::map<uint32_t,uint32_t> memory,palettes;
        for(unsigned i=0;i<5;++i)memory[lod+i]=descriptor[i];
        for(unsigned part=0;part<2;++part)
        {
            const auto address=descriptor[part?4:1],count=part?6*np:3*nv;
            for(uint32_t i=0;i<count;++i)
            {
                uint32_t value;if(!(std::cin>>value))return 2;
                auto old=memory.find(address+i);
                if(old!=memory.end() && old->second!=value)return 2;
                memory[address+i]=value;
            }
        }
        Model model;
        if(!load([&](uint32_t p){return memory.at(p);},lod,model))return 3;
        for(const auto &p:model.polygons)
        {
            uint32_t value;if(!(std::cin>>value))return 2;
            auto i=palettes.find(p[0]>>16);
            if(i!=palettes.end() && i->second!=value)return 2;
            palettes[p[0]>>16]=value;
        }
        if(prepared)
        {
            std::array<uint32_t,22> object;
            std::array<uint32_t,12> view,actual;
            std::array<uint32_t,13> context;
            for(auto &v:object)std::cin>>v;
            for(auto &v:view)std::cin>>v;
            for(auto &v:context)std::cin>>v;
            if(!std::cin || !cruisn::offroad_transform::prepare(object,view,
                [&](int32_t index){return trigonometry.at(index+1);},actual) || actual!=matrix)return 6;
            const auto selection=cruisn::offroad_transform::select_lod(object,context);
            if(uint64_t(object[20])+7+5*selection.first!=lod ||
                ((object[5]&0x20) && context[1]==context[2] && uint32_t(selection.second)!=object[9]))return 7;
            matrix=actual;
        }
        std::vector<Vertex> points;std::vector<Quad> output;
        if(!project(model,matrix,origin,path,[&](int32_t index){return reciprocals.at(index+4096);},points))return 4;
        if(!quads(model,points,extra,palette_base,texture_base,[&](uint32_t index){return palettes.at(index);},output))return 5;
        std::cout<<id<<' '<<points.size()<<' '<<output.size();
        for(const auto &p:points)for(auto w:p)std::cout<<' '<<w;
        for(const auto &q:output)for(auto w:q)std::cout<<' '<<w;
        std::cout<<'\n';
    }
    return std::cin.eof() && records?0:2;
}
