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
        if(argc!=5 || std::string(argv[1])!="--future")return 2;
        const auto ram=load(argv[2],0x80000),fast=load(argv[3],0x2000),rom=load(argv[4],0x1000000);
        auto read=[&](uint32_t p){if(p<ram.size())return ram[p];
            if(p>=0x809800 && p-0x809800<fast.size())return fast[p-0x809800];
            if(p>=0xc00000 && p-0xc00000<rom.size())return rom[p-0xc00000];
            throw std::runtime_error("unmapped USA future operand");};
        cruisn::usa_future::Result result;
        if(!cruisn::usa_future::code_matches(read))throw std::runtime_error("USA code signature rejected");
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
