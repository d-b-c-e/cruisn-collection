// license:BSD-3-Clause
// Offline entry for the exact same host helper used by the emulator adapter.
#include "world_host_scenery.h"
#include <iostream>
#include <map>
#include <string>
#include <stdexcept>
int main(int argc,char **argv)
{
    using cruisn::scenery::Float;
    if(argc==2 && std::string(argv[1])=="--math")
    {
        int32_t am,bm;int ae,be;
        while(std::cin>>am>>ae>>bm>>be)
        {
            Float a(am,ae),b(bm,be);
            for(auto f:{a+b,a-b,a*b,-a})std::cout<<f.m<<' '<<f.e<<' ';
            Float n=Float::integer(am);std::cout<<a.fix()<<' '<<n.m<<' '<<n.e<<'\n';
        }
        return 0;
    }
    if((argc!=2 && argc!=3) || std::string(argv[1])!="--scene")return 2;
    uint32_t far=argc==3?uint32_t(std::stoul(argv[2])):80000;
    std::map<uint32_t,uint32_t> memory;
    uint32_t address,value;
    while(std::cin>>address>>value)memory[address]=value;
    cruisn::world_host::Scene scene;
    try
    {
        if(!cruisn::world_host::build([&](uint32_t p)->uint32_t{
            auto i=memory.find(p);if(i==memory.end())throw std::runtime_error("uncaptured read "+std::to_string(p));
            return i->second;},scene,far))throw std::runtime_error("scene guard failed");
    }
    catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
    std::cout<<scene.pending<<' '<<scene.unsupported<<' '<<scene.distance<<' '<<scene.decoded<<'\n';
    for(const auto &o:scene.objects)for(const auto &q:o.quads)
    {
        std::cout<<o.id<<' '<<o.model<<' '<<o.depth<<' '<<o.section;
        for(auto v:q)std::cout<<' '<<v;
        std::cout<<'\n';
    }
}
