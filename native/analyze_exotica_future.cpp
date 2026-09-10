// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_future_sections.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
static std::vector<uint32_t> load(const char *path,size_t bytes)
{
    std::ifstream file(path,std::ios::binary|std::ios::ate);
    if(!file || file.tellg()!=std::streamoff(bytes))throw std::runtime_error("incomplete Exotica snapshot");
    file.seekg(0);std::vector<uint32_t> data(bytes/4);
    if(!file.read(reinterpret_cast<char *>(data.data()),bytes))throw std::runtime_error("Exotica snapshot read");
    return data;
}
int main(int argc,char **argv)
{
    try
    {
        if(argc!=6)return 2;
        const std::string bank_text=argv[4],partial_text=argv[5];
        if((bank_text!="0" && bank_text!="1" && bank_text!="2") || (partial_text!="0" && partial_text!="1"))return 2;
        const uint32_t bank=uint32_t(std::stoul(bank_text));
        const auto ram=load(argv[1],0x100000),main=load(argv[2],0x800000),banks=load(argv[3],0x3000000);
        auto read=[&](uint32_t p){
            if(p<0x40000)return ram[p];
            if(p>=0xa00000 && p<0xc00000)return main[p-0xa00000];
            if(p>=0xc00000 && p<0x1000000)return banks[bank*0x400000+p-0xc00000];
            throw std::runtime_error("unmapped Exotica source");};
        cruisn::exotica_future::Result result;
        if(!cruisn::exotica_future::build(read,result,partial_text=="1"))throw std::runtime_error("Exotica source/frontier rejected");
        std::cout<<result.pretrack<<' '<<result.partial<<' '<<result.frontier<<' '<<result.sections.size()<<' '<<result.sources.size()<<'\n';
        for(const auto &s:result.sources)
        {
            std::cout<<s.entry<<' '<<s.source<<' '<<s.index<<' '<<s.ordinal<<' '<<s.supported<<' '<<s.future;
            for(auto word:s.words)std::cout<<' '<<word;
            std::cout<<'\n';
        }
    }
    catch(const std::exception &error){std::cerr<<error.what()<<'\n';return 1;}
}
