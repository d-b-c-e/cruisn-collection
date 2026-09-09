// SPDX-License-Identifier: BSD-3-Clause
#include "usa_host_scenery.h"
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
int main(int argc,char **argv)
{
    if(argc!=3 || std::string(argv[1])!="--scene")return 2;
    const uint32_t far=uint32_t(std::stoul(argv[2]));
    std::map<uint32_t,uint32_t> memory;
    uint32_t address,value;
    while(std::cin>>address>>value)
    {
        if(memory.size()>=200000 || !memory.emplace(address,value).second)return 2;
    }
    if(!std::cin.eof() || memory.empty())return 2;
    cruisn::usa_host::Scene scene;
    try
    {
        if(!cruisn::usa_host::build([&](uint32_t p)
            {auto i=memory.find(p);if(i==memory.end())throw std::runtime_error("uncaptured read "+std::to_string(p));return i->second;},scene,far))
            throw std::runtime_error("USA pending scene rejected");
    }
    catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
    std::cout<<scene.pending<<' '<<scene.unsupported<<' '<<scene.near<<' '<<scene.far<<' '<<scene.projection<<' '<<scene.decoded<<'\n';
    for(const auto &o:scene.objects)for(const auto &q:o.quads)
    {
        std::cout<<o.id<<' '<<o.model<<' '<<o.depth;
        for(auto word:q)std::cout<<' '<<word;
        std::cout<<'\n';
    }
}
