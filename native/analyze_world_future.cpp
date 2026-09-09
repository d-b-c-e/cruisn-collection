// license:BSD-3-Clause
// Offline access to the future-section helper; raw resources remain local only.
#include "world_future_sections.h"
#include <fstream>
#include <iostream>
#include <string>
#include <stdexcept>
#include <chrono>

std::vector<uint32_t> load(const char *path,size_t count)
{
    std::ifstream f(path,std::ios::binary);std::vector<uint32_t> result(count);
    if(!f.read(reinterpret_cast<char *>(result.data()),count*4) || f.peek()!=EOF)
        throw std::runtime_error("invalid snapshot length");
    return result;
}
int main(int argc,char **argv)
{
    if(argc==2 && std::string(argv[1])=="--yaw")
    {
        int32_t m;int e;std::array<uint32_t,7> c;
        while(std::cin>>m>>e)
        {
            for(auto &v:c)if(!(std::cin>>v))return 2;
            for(auto v:cruisn::world_future::yaw({m,e},c))std::cout<<v<<' ';
            std::cout<<'\n';
        }
        return 0;
    }
    if((argc<6 || argc>8) || (std::string(argv[1])!="--descriptors" && std::string(argv[1])!="--scene"))return 2;
    bool roads=false;uint32_t revision=24;
    for(int i=6;i<argc;++i){if(std::string(argv[i])=="--roads")roads=true;
        else if(std::string(argv[i])=="--world25")revision=25;else return 2;}
    try
    {
        auto ram=load(argv[2],0x20000),rom=load(argv[3],0x400000),fast=load(argv[4],0x800);
        auto read=[&](uint32_t p)->uint32_t{
            if(p<0x20000)return ram[p];
            if(p>=0xc00000 && p<0x1000000)return rom[p-0xc00000];
            if(p>=0x809800 && p<0x80a000)return fast[p-0x809800];
            throw std::runtime_error("unmapped snapshot read "+std::to_string(p));};
        cruisn::world_future::Cache cache;
        std::vector<cruisn::world_host::Descriptor> descriptors;
        cruisn::world_future::Stats stats;
        auto begin=std::chrono::steady_clock::now();
        if(!cruisn::world_future::code_matches(read,revision))throw std::runtime_error("revision code guard failed");
        if(roads && !cruisn::world_road::code_matches(read))throw std::runtime_error("road code guard failed");
        if(!cruisn::world_future::collect(read,cache,descriptors,stats,64,roads,revision))throw std::runtime_error("future guard failed");
        auto built=std::chrono::steady_clock::now();
        std::vector<cruisn::world_host::Descriptor> repeat;cruisn::world_future::Stats warm;
        if(!cruisn::world_future::collect(read,cache,repeat,warm,64,roads,revision) || repeat.size()!=descriptors.size() || warm.new_sections)
            throw std::runtime_error("warm cache mismatch");
        for(size_t i=0;i<repeat.size();++i)if(repeat[i].id!=descriptors[i].id || repeat[i].words!=descriptors[i].words)
            throw std::runtime_error("warm descriptor mismatch");
        auto ready=std::chrono::steady_clock::now();
        std::cerr<<"cold_us "<<std::chrono::duration<double,std::micro>(built-begin).count()
                 <<" warm_us "<<std::chrono::duration<double,std::micro>(ready-built).count()<<'\n';
        std::cout<<stats.sections<<' '<<stats.definitions<<' '<<stats.skipped<<' '<<stats.special<<' '
                 <<stats.unbound<<' '<<stats.ready<<' '<<stats.new_sections<<'\n';
        if(std::string(argv[1])=="--descriptors")
        {
            for(const auto &kv:cache.sections)for(const auto &source:kv.second.sources)
                for(const auto &d:descriptors)if(source.descriptor.id==d.id)
                {std::cout<<kv.first<<' '<<source.source<<' '<<d.id;for(auto v:d.words)std::cout<<' '<<v;std::cout<<'\n';break;}
        }
        else
        {
            cruisn::world_host::Scene scene;
            if(!cruisn::world_host::build(read,scene,uint32_t(std::stoul(argv[5])),&descriptors,roads,revision))
                throw std::runtime_error("future projection guard failed");
            for(const auto &object:scene.objects)for(const auto &quad:object.quads)
            {
                std::cout<<object.id<<' '<<object.model<<' '<<object.depth<<' '<<object.section;
                for(auto v:quad)std::cout<<' '<<v;
                std::cout<<'\n';
            }
        }
    }
    catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
