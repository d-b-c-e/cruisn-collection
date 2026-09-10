// SPDX-License-Identifier: BSD-3-Clause
#include "zeus_state.h"
#include <iostream>
#include <cstring>
using cruisn::zeus_state::Context;
uint32_t bits(float f){uint32_t w;std::memcpy(&w,&f,4);return w;}
void read_float(float &f){uint32_t w=0;std::cin>>w;std::memcpy(&f,&w,4);}
void read(Context &c)
{
    std::cin>>c.quad_size>>c.ucode>>c.palette>>c.texture>>c.yscale>>c.zoffset;
    for(auto &f:c.matrix)read_float(f);
    for(auto &f:c.translation)read_float(f);
    for(auto &f:c.light)read_float(f);
    for(auto &w:c.regs)std::cin>>w;
    for(auto &w:c.render)std::cin>>w;
}
void print(const Context &c)
{
    std::cout<<' '<<c.quad_size<<' '<<c.ucode<<' '<<c.palette<<' '<<c.texture<<' '<<c.yscale<<' '<<c.zoffset;
    for(auto f:c.matrix)std::cout<<' '<<bits(f);
    for(auto f:c.translation)std::cout<<' '<<bits(f);
    for(auto f:c.light)std::cout<<' '<<bits(f);
    for(auto w:c.regs)std::cout<<' '<<w;
    for(auto w:c.render)std::cout<<' '<<w;
}
int main()
{
    uint32_t id,previous=0;unsigned count=0;
    while(std::cin>>id)
    {
        if(++count>4096 || id<=previous)return 2;
        previous=id;Context c;read(c);unsigned n=0;std::cin>>n;
        if(!std::cin || n>2*(0xc800+1) || n%2)return 2;
        std::vector<uint32_t> model(n);for(auto &w:model)std::cin>>w;
        std::cin>>n;if(!std::cin || n<4 || n>128)return 2;
        std::vector<uint32_t> setup(n);for(auto &w:setup)std::cin>>w;
        uint32_t base=0;std::cin>>base;cruisn::zeus_state::Result result;
        if(!std::cin || !cruisn::zeus_state::transition(c,model,setup,base,result))return 2;
        std::cout<<id;print(result.context);std::cout<<' '<<result.loads.size();
        for(auto l:result.loads)std::cout<<' '<<l.kind<<' '<<l.source<<' '<<l.control;
        std::cout<<'\n';
    }
    return count && std::cin.eof()?0:2;
}
