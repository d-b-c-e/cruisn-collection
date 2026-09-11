// SPDX-License-Identifier: BSD-3-Clause
// Bounded generic lifetime-event stream. Raw guest data is supplied locally.
#include "scenery_lifetimes.h"
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace cruisn::scenery_lifetimes;
static uint64_t number(const std::string &s) {
    if(s.empty())throw std::runtime_error("empty integer");
    uint64_t value=0;
    for(const char c:s) {
        if(c<'0' || c>'9' || value>(UINT64_MAX-uint64_t(c-'0'))/10)throw std::runtime_error("unsigned integer");
        value=value*10+unsigned(c-'0');
    }
    return value;
}
static bool read_line(std::istream &in,std::string &line) {
    line.clear();char c;
    while(in.get(c)) {
        if(c=='\n')return true;
        if(line.size()==256)throw std::runtime_error("line budget");
        line+=c;
    }
    if(in.bad())throw std::runtime_error("event input failed");
    return !line.empty();
}
int main(int argc,char **) {
    if(argc!=1)return 2;
    std::ios::sync_with_stdio(false);
    size_t line_number=0;
    try {
        Registry registry;std::string line;
        while(read_line(std::cin,line)) {
            if(++line_number>200000 || line.size()>256)throw std::runtime_error("event budget");
            std::istringstream in(line);std::string op,token;in>>op;std::vector<uint64_t> v;
            while(in>>token) {if(v.size()>=8)throw std::runtime_error("operand budget");v.push_back(number(token));}
            auto u32=[&](size_t i){if(i>=v.size() || v[i]>UINT32_MAX)throw std::runtime_error("32-bit operand");return uint32_t(v[i]);};
            auto key=[&](size_t i){Key k;k.realm=v.at(i);k.section=u32(i+1);k.source=u32(i+2);return k;};
            auto layout=[&](){Layout l;l.first=u32(0);l.last=u32(1);l.max_tracked=u32(2);return l;};
            uint64_t generation=0;bool flag=false,accepted=false;Handle h;
            if(op=="L" && v.size()==4 && line_number==1 && v[3]<=1)accepted=registry.start(layout(),v[3]!=0);
            else if(op=="A" && v.size()==1)accepted=registry.allocate(u32(0),generation);
            else if(op=="F" && v.size()==1)accepted=registry.release(u32(0),flag);
            else if(op=="R" && v.size()==3)accepted=registry.reset(layout());
            else if(op=="B" && v.size()==4) {accepted=registry.bind(u32(0),key(1),h);generation=h.generation;}
            else if(op=="D" && v.size()==7) {
                h.slot=u32(0);h.epoch=v[1];h.generation=v[2];h.key=key(3);generation=h.generation;
                accepted=registry.submitted(h,v[6],flag);
            }
            if(!accepted)throw std::runtime_error("event rejected");
            std::cout<<op<<' '<<registry.sequence()<<' '<<registry.epoch()<<' '<<generation<<' '<<unsigned(flag)<<'\n';
        }
        if(std::cin.bad() || !line_number)throw std::runtime_error("missing or failed event input");
        std::cout.flush();if(!std::cout)throw std::runtime_error("event output failed");
    } catch(const std::exception &error) {
        std::cerr<<"line "<<line_number<<": "<<error.what()<<'\n';return 1;
    }
}
