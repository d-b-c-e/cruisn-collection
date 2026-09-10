// SPDX-License-Identifier: BSD-3-Clause
// copyright-holders:Aaron Giles
// Private Exotica state transitions from zeus2.cpp. BSD notice: scenery_c31.py.
// Load requests describe required resources; they do not certify residency/colors.
#pragma once
#include "scenery_c31.h"
#include <vector>
#include <cmath>
namespace cruisn { namespace zeus_state {
struct Context
{
    uint32_t quad_size=10,ucode=0,palette=0,texture=0,yscale=0,zoffset=0;
    std::array<float,9> matrix{};
    std::array<float,4> translation{};
    std::array<float,3> light{};
    std::array<uint32_t,128> regs{};
    std::array<uint32_t,80> render{};
};
struct Load { uint32_t kind,source,control; };
struct Result { Context context;std::vector<Load> loads; };
inline float floating(uint32_t w)
{
    const auto f=scenery::Float::load(w);
    return f.e==-128?0.0f:float(std::ldexp(double(int64_t(f.m)^INT64_C(0x80000000)),f.e-31));
}
inline bool valid(const Context &c)
{
    if((c.quad_size!=10 && c.quad_size!=12 && c.quad_size!=14) || c.yscale>1 || c.zoffset)return false;
    for(auto f:c.matrix)if(!std::isfinite(f))return false;
    for(auto f:c.translation)if(!std::isfinite(f))return false;
    for(auto f:c.light)if(!std::isfinite(f))return false;
    return true;
}
inline bool pointer(Context &c,uint32_t word)
{
    const unsigned p=word>>24;const uint32_t value=word&0xffffff;
    if(p>=80 || p==8)return false;
    c.regs[0x20]=word;c.render[p]=value;
    if(p==1 || p==2)c.render[p]&=0xfff;
    if(p==5)c.texture=value%(1024*2048);
    return true;
}
inline bool transition(const Context &previous,const std::vector<uint32_t> &model,
    const std::vector<uint32_t> &packet,uint32_t base,Result &output)
{
    const Context input=previous; // Permit output.context as the previous context.
    output=Result();if(!valid(input) || model.size()%2 || model.size()>2*(0xc800+1) ||
        packet.size()<4 || packet.size()>128)return false;
    Result r;r.context=input;auto &c=r.context;
    for(size_t i=0;i<model.size();)
    {
        const auto *d=&model[i];unsigned cmd=d[0]>>24,n=cmd==0x38?c.quad_size:2;
        if(i+n>model.size())return false;
        i+=n;c.regs[0x19]+=n;
        if(cmd==0 || cmd==0x22)c.regs[0x68]=(d[0]>>16)&255;
        else if(cmd==0x36){if(((d[0]>>16)&127)!=0x20 || !pointer(c,d[1]))return false;}
        else if(cmd!=0x38)return false;
    }
    for(size_t i=0;i<packet.size();)
    {
        const auto *d=&packet[i];unsigned cmd=d[0]>>24,n=0;
        switch(cmd){case 0x32:n=1;break;case 5:n=2;break;case 7:n=13;break;case 0x16:case 0x1c:n=4;break;}
        if(!n || i+n>packet.size())return false;
        i+=n;c.regs[0x18]+=n;
        if(cmd==0x32)continue;
        if(cmd==7)
        {
            for(unsigned j=0;j<9;++j)c.matrix[j]=floating(d[j+1]);
            for(unsigned j=0;j<3;++j)c.translation[j]=floating(d[j+10]);
        }
        else if(cmd==0x16){for(unsigned j=0;j<3;++j)c.translation[j]=floating(d[j+1]);}
        else if(cmd==0x1c){for(unsigned j=0;j<3;++j)c.light[j]=floating(d[j+1]);}
        else
        {
            const unsigned reg=(d[0]>>16)&127;const uint32_t value=d[1];
            if(reg!=0x20 && reg!=0x40 && reg!=0x41)return false;
            c.regs[reg]=value;
            if(reg==0x20){if(!pointer(c,value))return false;}
            else if(reg==0x41)c.regs[reg]&=0x1fff03ff;
            else
            {
                if(c.regs[0x4e]&15)return false;
                const unsigned code=(value>>16)&15;const uint32_t address=c.regs[0x41];
                if(code==5)
                {
                    if(value>>24>=0xc0)return false;
                    switch(address){case 0xc0:c.quad_size=10;break;case 0x136:c.quad_size=14;break;
                        case 0x22b:case 0x29b:c.quad_size=12;break;default:return false;}
                    c.ucode=address;c.zoffset=0;
                }
                else if(code==4)c.palette=address%1024+((address>>16)%2048)*1024;
                else return false;
                r.loads.push_back({code,address,value});
            }
        }
    }
    c.regs[0x18]+=2;c.regs[8]=base;
    if(!valid(c))return false;
    output=std::move(r);return true;
}
} }
