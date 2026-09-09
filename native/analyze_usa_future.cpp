// SPDX-License-Identifier: BSD-3-Clause
#include "usa_future_sections.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
static std::vector<uint32_t> load(const char *path,size_t bytes)
{
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f || f.tellg()!=std::streamoff(bytes))throw std::runtime_error("incomplete snapshot");
    f.seekg(0);std::vector<uint32_t> words(bytes/4);
    if(!f.read(reinterpret_cast<char *>(words.data()),bytes))throw std::runtime_error("snapshot read failed");
    return words;
}
int main(int argc,char **argv)
{
    try
    {
        if(argc<2)return 2;
        const std::string mode=argv[1];const bool scene_mode=mode=="--scene";
        if((scene_mode && argc!=6) || (!scene_mode && (argc!=5 || (mode!="--future" && mode!="--collect"))))return 2;
        const unsigned offset=scene_mode?3:2;
        const auto ram=load(argv[offset],0x80000),fast=load(argv[offset+1],0x2000),rom=load(argv[offset+2],0x1000000);
        auto read=[&](uint32_t p){if(p<ram.size())return ram[p];
            if(p>=0x809800 && p-0x809800<fast.size())return fast[p-0x809800];
            if(p>=0xc00000 && p-0xc00000<rom.size())return rom[p-0xc00000];
            throw std::runtime_error("unmapped USA future operand");};
        if(!cruisn::usa_future::code_matches(read))throw std::runtime_error("USA code signature rejected");
        if(mode!="--future")
        {
            cruisn::usa_future::Cache cache;cruisn::usa_future::Stats stats;
            std::vector<cruisn::usa_host::Descriptor> descriptors;
            if(!cruisn::usa_future::collect(read,cache,descriptors,stats))throw std::runtime_error("USA collection rejected");
            std::cout<<stats.start<<' '<<stats.loading<<' '<<stats.number<<' '<<stats.partial<<' '<<stats.pretrack<<' '
                <<stats.sections<<' '<<stats.definitions<<' '<<stats.special<<' '<<stats.unbound<<' '<<stats.deferred<<' '<<stats.ready<<' '<<stats.uploads<<'\n';
            if(scene_mode)
            {
                cruisn::usa_host::Scene scene;cruisn::usa_host::ModelCache models;
                // Exercise both cold and warm ROM caches against the same independent oracle.
                for(unsigned pass=0;pass<2;++pass)
                    if(!cruisn::usa_host::build(read,scene,uint32_t(std::stoul(argv[2])),&descriptors,&models))throw std::runtime_error("USA scene rejected");
                std::cout<<scene.pending+scene.future<<' '<<scene.unsupported<<' '<<scene.near<<' '<<scene.far<<' '<<scene.projection<<' '<<scene.decoded<<'\n';
                for(const auto &o:scene.objects)for(const auto &q:o.quads)
                {std::cout<<o.id<<' '<<o.model<<' '<<o.depth;for(auto word:q)std::cout<<' '<<word;std::cout<<'\n';}
            }
            else for(const auto &d:descriptors)
            {std::cout<<d.id;for(auto word:d.words)std::cout<<' '<<word;std::cout<<'\n';}
            return 0;
        }
        cruisn::usa_future::Result result;
        if(!cruisn::usa_future::build(read,result))throw std::runtime_error("USA frontier rejected");
        std::cout<<result.start<<' '<<result.loading<<' '<<result.number<<' '<<result.partial<<' '
            <<result.pretrack<<' '<<result.end<<' '<<result.sources.size()<<'\n';
        for(const auto &s:result.sources)
        {
            std::cout<<s.section<<' '<<s.source<<' '<<s.stage<<' '<<s.number<<' '
                <<s.supported<<' '<<s.resident<<' '<<s.prefix<<' '<<s.binding;
            for(auto v:s.words)std::cout<<' '<<v;
            std::cout<<'\n';
        }
    }
    catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
