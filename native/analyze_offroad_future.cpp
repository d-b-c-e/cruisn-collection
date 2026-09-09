// SPDX-License-Identifier: BSD-3-Clause
#include "offroad_host_scenery.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
static std::vector<uint32_t> load(const char *path,size_t bytes)
{
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f || f.tellg()!=std::streamoff(bytes))throw std::runtime_error("incomplete Off Road snapshot");
    f.seekg(0);std::vector<uint32_t> words(bytes/4);
    if(!f.read(reinterpret_cast<char *>(words.data()),bytes))throw std::runtime_error("snapshot read failed");
    return words;
}
int main(int argc,char **argv)
{
    try
    {
        const bool scene_mode=argc==6 && std::string(argv[1])=="--scene";
        if(!scene_mode && (argc!=4 || (std::string(argv[1])!="--future" && std::string(argv[1])!="--loaded")))return 2;
        const unsigned offset=scene_mode?4:2;
        const auto ram=load(argv[offset],0x80000),rom=load(argv[offset+1],0x1000000);
        auto read=[&](uint32_t p){if(p<ram.size())return ram[p];
            if(p>=0xc00000 && p-0xc00000<rom.size())return rom[p-0xc00000];
            throw std::runtime_error("unmapped Off Road source");};
        if(!cruisn::offroad_future::code_matches(read))throw std::runtime_error("Off Road revision rejected");
        if(scene_mode)
        {
            const std::string mode=argv[3];if(mode!="pending" && mode!="future")return 2;
            const uint32_t multiplier=uint32_t(std::stoul(argv[2]));
            cruisn::offroad_host::Cache cache;cruisn::offroad_host::Scene scene;
            for(unsigned pass=0;pass<2;++pass)
            {
                if(!cruisn::offroad_host::build(read,scene,multiplier,mode=="future",cache))
                    throw std::runtime_error("Off Road host scene rejected");
                std::cout<<scene.pending<<' '<<scene.future<<' '<<scene.unsupported<<' '<<scene.near<<' '<<scene.far<<' '
                    <<scene.projection<<' '<<scene.material<<' '<<scene.pretrack<<' '<<scene.partial<<' '<<scene.deferred<<' '<<scene.objects.size()<<'\n';
                for(const auto &o:scene.objects)for(const auto &q:o.quads)
                {
                    std::cout<<o.id<<' '<<o.model<<' '<<o.lod<<' '<<o.depth<<' '<<o.order;
                    for(auto word:q)std::cout<<' '<<word;
                    std::cout<<'\n';
                }
                std::cout<<"end\n";
            }
            return 0;
        }
        cruisn::offroad_future::Result r;
        if(!cruisn::offroad_future::build(read,r,std::string(argv[1])=="--loaded"))
            throw std::runtime_error("Off Road frontier/source rejected");
        const auto &f=r.frontier;
        std::cout<<f.track<<' '<<f.count<<' '<<f.current<<' '<<f.front<<' '<<f.back<<' '<<f.pretrack<<' '<<f.partial<<' '<<r.sources.size()<<'\n';
        for(const auto &s:r.sources)
        {
            std::cout<<s.entry<<' '<<s.source<<' '<<s.number<<' '<<s.ordinal<<' '<<s.flags<<' '<<s.supported;
            for(auto word:s.words)std::cout<<' '<<word;
            std::cout<<'\n';
        }
    }
    catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
