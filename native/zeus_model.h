// SPDX-License-Identifier: BSD-3-Clause
// copyright-holders:Aaron Giles
// Read-only Zeus2 packed model/projection semantics adapted from MAME zeus2.cpp
// and poly.h. Full BSD notice: harness/scenery_c31.py. No guest/game data.
// Context is copied: model-local register writes never reach the real device.
#pragma once
#include <array>
#include <vector>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <cstring>
#include "zeus_render_policy.h"
namespace cruisn { namespace zeus_model {
struct Context
{
    uint32_t frame=0,quad_size=10,texture=0,yscale=0,render_policy=0;
    std::array<float,9> matrix{};
    std::array<float,3> translation{};
    std::array<uint32_t,128> regs{};
    std::array<uint32_t,80> render{};
};
struct Quad
{
    std::array<uint32_t,17> state{};
    std::array<std::array<float,6>,8> vertices{};
};
static_assert(sizeof(Quad)==260,"Zeus projected record layout");
struct Result
{
    std::vector<Quad> quads;
    unsigned polygons=0,near_rejected=0,backfaces=0,near_clipped=0,register_writes=0;
};
inline float word_float(uint32_t value)
{
    float f;static_assert(sizeof(f)==sizeof(value),"float word size");
    std::memcpy(&f,&value,sizeof(f));return f;
}
using Vertex=std::array<float,6>;
inline int project(const uint32_t *d,uint32_t tex,const Context &ctx,Quad &quad)
{
    const int vs=int(ctx.regs[0x66])-0x8e,us=int(ctx.regs[0x68])-0x9d;
    if(vs<-31 || vs>31 || us<-31 || us>31 || ctx.regs[0x6c]>30)return -1;
    const float scale=std::ldexp(1.0f,vs),uvscale=std::ldexp(1.0f,us);
    const float clip=word_float(ctx.regs[0x78]),ox=word_float(ctx.regs[0x6a]),oy=word_float(ctx.regs[0x6b]);
    if(!std::isfinite(clip) || !std::isfinite(ox) || !std::isfinite(oy))return -1;
    const int32_t xyz[4][3]={{int16_t(d[2]),int16_t(d[3]),int16_t(d[6])},
        {int16_t(d[2]>>16),int16_t(d[3]>>16),int16_t(d[6]>>16)},
        {int16_t(d[8]),int16_t(d[9]),int16_t(d[7])},
        {int16_t(d[8]>>16),int16_t(d[9]>>16),int16_t(d[7]>>16)}};
    const uint32_t uv[4][2]={{d[1]&1023,(d[1]>>16)&1023},{d[4]&1023,(d[4]>>10)&1023},
        {(d[4]>>20)&1023,d[5]&1023},{(d[5]>>10)&1023,(d[5]>>20)&1023}};
    std::array<Vertex,4> input{};
    for(unsigned i=0;i<4;++i)
    {
        const float x=xyz[i][0]*scale,y=xyz[i][1]*scale,z=xyz[i][2]*scale;
        for(unsigned row=0;row<3;++row)
            input[i][row]=((x*ctx.matrix[3*row]+y*ctx.matrix[3*row+1])+z*ctx.matrix[3*row+2])+ctx.translation[row];
        input[i][3]=(float(uv[i][0])*uvscale)*256.0f;
        input[i][4]=(float(uv[i][1])*uvscale+float(tex>>16))*256.0f;
    }
    std::array<Vertex,8> output{};unsigned count=0;
    Vertex previous=input[3];bool prior=previous[2]<clip,any_clipped=prior;
    for(const auto &v:input)
    {
        const bool outside=v[2]<clip;any_clipped|=outside;
        if(outside!=prior)
        {
            const float fraction=(clip-previous[2])/(v[2]-previous[2]);
            if(count>=8)return -1;
            for(unsigned j=0;j<6;++j)output[count][j]=previous[j]+fraction*(v[j]-previous[j]);
            ++count;
        }
        if(!outside){if(count>=8)return -1;output[count++]=v;}
        previous=v;prior=outside;
    }
    if(count<3)return 0;
    for(unsigned i=0;i<count;++i)
    {
        auto &v=output[i];if(v[2]<0)v[2]=0;
        const float ooz=float(1U<<ctx.regs[0x6c])/(v[2]+2.0f);
        v[0]=v[0]*ooz+ox;v[1]=v[1]*ooz+oy;
        v[2]*=4096.0f;v[3]*=ooz;v[4]*=ooz;v[5]=ooz;
        for(auto value:v)if(!std::isfinite(value))return -1;
    }
    const auto &a=output[0],&b=output[1],&c=output[2];
    if((a[1]-b[1])*(b[0]-c[0])-(a[0]-b[0])*(b[1]-c[1])>=0)return 1;
    const uint32_t mode=tex&65535,type=mode&3;const bool alpha=type==2 && (mode&0x80);
    const auto mat=zeus_policy::material(ctx.render_policy,mode,ctx.render[0x14],ctx.render[0x40],ctx.render[0xc]);
    uint32_t flags=((mode&0xc00)==0xc00?1:0)|4;
    if(ctx.render_policy&zeus_policy::DepthFloor)flags|=zeus_policy::QuadDepthFloor;
    if(mat.blend)flags|=2;
    if(mat.depth_test)flags|=8;
    if(mat.depth_write)flags|=16;
    if(ctx.render[0x14]&0xc00)flags|=32;
    if(alpha)flags|=64;
    if(type==2 && !alpha)flags|=128;
    uint32_t width=0x20<<((mode>>2)&3);if(type==0)width>>=1;
    const uint32_t bias=uint32_t(int32_t(ctx.render[0x15]<<8)>>8);
    quad.state={{ctx.frame,count,tex,ctx.texture,width,ctx.regs[0]&0x7fff,
        (mode&0x180)?0U:0x100U,mat.source_alpha,std::min(ctx.render[0xd],0x100U),
        flags,bias,ctx.render[4],ctx.yscale,0,0,ctx.render[1]&0xfff,ctx.render[2]&0xfff}};
    quad.vertices=output;return any_clipped?3:2;
}
inline bool decode(const std::vector<uint32_t> &words,Context context,Result &result)
{
    result=Result();
    if(words.size()>2*(0xc800+1) || words.size()%2 || context.yscale>1 || context.render_policy>7 ||
        (context.quad_size!=10 && context.quad_size!=12 && context.quad_size!=14))return false;
    for(auto f:context.matrix)if(!std::isfinite(f))return false;
    for(auto f:context.translation)if(!std::isfinite(f))return false;
    uint32_t tex=0;
    for(size_t i=0;i<words.size();)
    {
        const uint32_t *d=words.data()+i,cmd=d[0]>>24;
        const unsigned length=cmd==0x38?context.quad_size:2;
        if(length>words.size()-i)return false;
        i+=length;
        if(cmd==0 || cmd==0x22){context.regs[0x68]=(d[0]>>16)&255;tex=d[1];}
        else if(cmd==0x36)
        {
            const uint32_t reg=(d[0]>>16)&127,pointer=d[1]>>24,value=d[1]&0xffffff;
            // Palette loads require separate live material ownership/readiness.
            if(reg!=0x20 || pointer>=80 || pointer==8)return false;
            context.regs[reg]=d[1];context.render[pointer]=value;++result.register_writes;
            if(pointer==5)context.texture=value%(1024*2048);
            if(pointer==1 || pointer==2)context.render[pointer]&=0xfff;
        }
        else if(cmd==0x38)
        {
            ++result.polygons;Quad quad;const int status=project(d,tex,context,quad);
            if(status<0)return false;
            if(status==0)++result.near_rejected;
            else if(status==1)++result.backfaces;
            else{if(status==3)++result.near_clipped;result.quads.push_back(quad);}
        }
        else return false;
    }
    return true;
}
} }
