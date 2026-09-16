// SPDX-License-Identifier: BSD-3-Clause
// Bounded text protocol for independent replay of observed model-frame updates.
#include "exotica_animation.h"
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
            } else throw std::runtime_error("record kind");
        }
        if(!events)throw std::runtime_error("empty event stream");
    } catch(const std::exception &e) {std::cerr<<e.what()<<'\n';return 1;}
}
