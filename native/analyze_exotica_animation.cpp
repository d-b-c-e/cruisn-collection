// SPDX-License-Identifier: BSD-3-Clause
// Bounded text protocol for independent replay of observed model-frame updates.
#include "exotica_animation.h"
#include "exotica_animation_source.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace cruisn::exotica_animation;
uint32_t word()
{
    uint64_t n;
    if(!(std::cin>>n) || n>0xffffffffULL)throw std::runtime_error("invalid word");
    return uint32_t(n);
}
int main()
{
    try {
        std::map<uint32_t,Sequence> tables;char kind;unsigned events=0;
        while(std::cin>>kind) {
            if(kind=='T') {
                const auto key=word(),header=word(),count=word();
                if(tables.size()>=32 || tables.count(key) || count<2 || count>257)
                    throw std::runtime_error("table identity or size");
                std::vector<uint32_t> words;for(unsigned i=0;i<count;++i)words.push_back(word());
                Sequence s;if(!decode(header,words,s))throw std::runtime_error("table decode");
                tables.emplace(key,s);
            } else if(kind=='E') {
                const auto key=word();State a,b;a.remaining=word();a.cursor=word();a.model=word();
                if(++events>8192 || !tables.count(key) || !step(tables.at(key),a,b))
                    throw std::runtime_error("event decode");
                std::cout<<b.remaining<<' '<<b.cursor<<' '<<b.model<<'\n';
            } else if(kind=='I') {
                std::array<uint32_t,6> d,model;
                for(auto &v:d)v=word();
                for(auto &v:model)v=word();
                cruisn::exotica_future::Section section;
                section.flags=word();section.gap=word();section.cursor=word();section.index=word();
                const auto initial=word();if(initial>1)throw std::runtime_error("initial flag");
                section.initial=initial!=0;
                for(auto &v:section.header)v=word();
                for(auto &v:section.position)v=word();
                section.heading=word();section.section_heading=word();
                for(auto &v:section.matrix)v=word();
                std::array<uint32_t,11> constants;for(auto &v:constants)v=word();
                std::array<uint32_t,7> trig;for(auto &v:trig)v=word();
                std::array<uint32_t,2> materials;for(auto &v:materials)v=word();
                const auto node=word();cruisn::exotica_future::Source source;
                if(++events>8192 || !initial_fields(d,model,section,constants,trig,materials,node,source) || source.supported)
                    throw std::runtime_error("initial fields");
                for(size_t i=0;i<source.words.size();++i)std::cout<<(i?" ":"")<<source.words[i];
                std::cout<<'\n';
            } else throw std::runtime_error("record kind");
        }
        if(!events)throw std::runtime_error("empty event stream");
    } catch(const std::exception &e) {std::cerr<<e.what()<<'\n';return 1;}
}
