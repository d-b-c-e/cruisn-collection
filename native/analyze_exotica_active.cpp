// SPDX-License-Identifier: BSD-3-Clause
// Bounded LOCAL active-list operand stream; outputs ordered scalar decisions.
#include "exotica_active.h"
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
int main(int argc,char **argv)
{
    try
    {
        if(argc!=3)return 2;
        std::ifstream in(argv[1],std::ios::binary|std::ios::ate);
        if(!in || in.tellg()>32*1024*1024 || in.tellg()<8)throw std::runtime_error("active input size");
        in.seekg(0);
        auto word=[&](){uint32_t w;if(!in.read(reinterpret_cast<char *>(&w),4))throw std::runtime_error("truncated active operands");return w;};
        if(word()!=0x31454341)throw std::runtime_error("active input magic");
        const auto count=word();if(!count || count>512)throw std::runtime_error("active list budget");
        std::vector<std::array<uint32_t,12>> output;size_t candidates=0;
        for(unsigned i=0;i<count;++i)
        {
            const uint32_t entry=word(),head=word();
            cruisn::exotica_active::Parameters p;p.mode=word();p.margin=word();p.projection_table=word();
            for(auto &w:p.camera)w=word();for(auto &w:p.view)w=word();for(auto &w:p.alternate)w=word();for(auto &w:p.constants)w=word();
            if(uint64_t(p.projection_table)+5000>0x40000)throw std::runtime_error("active table bounds");
            std::map<uint32_t,uint32_t> memory;
            for(unsigned j=0;j<5000;++j)memory[p.projection_table+j]=word();
            const auto objects=word();if(objects>4096)throw std::runtime_error("active object budget");
            std::vector<uint32_t> expected;
            for(unsigned j=0;j<objects;++j)
            {
                const uint32_t object=word();if(object<0x1000 || uint64_t(object)+31>0x40000)throw std::runtime_error("active object range");
                expected.push_back(object);
                for(unsigned k=0;k<31;++k)if(!memory.emplace(object+k,word()).second)throw std::runtime_error("overlapping active operands");
            }
            if(!memory.emplace(head,expected.empty()?0:expected[0]).second)throw std::runtime_error("overlapping active head");
            auto read=[&](uint32_t a){return memory.at(a);};
            std::vector<cruisn::exotica_active::Source> sources;
            if(!cruisn::exotica_active::read_list(entry,head,read,sources) || sources.size()!=expected.size())throw std::runtime_error("active list reconstruction");
            for(unsigned j=0;j<sources.size();++j)
            {
                const auto &s=sources[j];if(s.source!=expected[j])throw std::runtime_error("active iteration order");
                cruisn::exotica_active::Decision d;
                if(!cruisn::exotica_active::classify(s,p,read,d))throw std::runtime_error("active classification");
                output.push_back({{s.entry,s.source,uint32_t(d.stock),uint32_t(d.wide),d.flags,uint32_t(d.depth),d.index,d.factor,d.translation[0],d.translation[1],d.translation[2],uint32_t(d.margin_candidate)}});
                candidates+=d.margin_candidate;
            }
            if(output.size()>65536)throw std::runtime_error("active total budget");
        }
        if(in.peek()!=std::char_traits<char>::eof())throw std::runtime_error("active trailing data");
        std::ofstream out(argv[2],std::ios::binary);
        if(!out.write(reinterpret_cast<const char *>(output.data()),output.size()*sizeof(output[0])))throw std::runtime_error("active output write");
        out.close();if(!out)throw std::runtime_error("active output close");
        std::cout<<"{\"passed\":true,\"lists\":"<<count<<",\"objects\":"<<output.size()<<",\"margin_candidates\":"<<candidates<<"}\n";
    }
    catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
