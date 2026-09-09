// SPDX-License-Identifier: BSD-3-Clause
// Off Road 1.63: five-word LOD descriptors, floating vertices, six-word polygons.
// This codec reproduces captured ordinary projection and DMA. Scene selection,
// transform preparation, clipping, residency and extended host drawing are separate.
#pragma once
#include "scenery_c31.h"
#include <vector>

namespace cruisn { namespace offroad_model {
using scenery::Float;
using Quad=std::array<uint16_t,16>;
using Vertex=std::array<uint32_t,2>;
struct Model
{
    std::vector<std::array<uint32_t,3>> vertices;
    std::vector<std::array<uint32_t,6>> polygons;
};
inline bool rom_span(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=8192 && uint64_t(p)+n<=0x1000000;}

template<class Read> bool load(Read read,uint32_t descriptor,Model &result)
{
    result=Model{};
    if(!rom_span(descriptor,5))return false;
    const uint32_t vertices=read(descriptor)+1,polygons=read(descriptor+3)+1;
    const uint32_t v=read(descriptor+1),p=read(descriptor+4);
    if(!vertices || vertices>512 || !polygons || polygons>1024 ||
        !rom_span(v,3*vertices) || !rom_span(p,6*polygons))return false;
    Model model;
    for(uint32_t i=0;i<vertices;++i)
        model.vertices.push_back({{read(v+3*i),read(v+3*i+1),read(v+3*i+2)}});
    for(uint32_t i=0;i<polygons;++i)
    {
        std::array<uint32_t,6> row;
        for(unsigned j=0;j<6;++j)row[j]=read(p+6*i+j);
        for(unsigned j:{4U,5U})for(unsigned shift:{0U,16U})
        {
            const auto offset=(row[j]>>shift)&65535;
            if(offset%3 || offset>=3*vertices)return false;
        }
        model.polygons.push_back(row);
    }
    result=std::move(model);return true;
}

template<class Reciprocal> bool project(const Model &model,
    const std::array<uint32_t,12> &matrix,uint32_t origin,uint32_t path,
    Reciprocal reciprocal,std::vector<Vertex> &result,uint32_t host_multiplier=0)
{
    result.clear();
    if(model.vertices.empty() || model.vertices.size()>512)return false;
    if(path!=0x1e03 && path!=0x1e3b && path!=0x1e60)return false;
    if(host_multiplier>3 || (host_multiplier && path!=0x1e03))return false;
    std::array<Float,12> m;
    for(unsigned i=0;i<12;++i)m[i]=Float::load(matrix[i]);
    std::vector<Vertex> points;
    for(const auto &vertex:model.vertices)
    {
        const std::array<Float,3> v={{Float::load(vertex[0]),Float::load(vertex[1]),Float::load(vertex[2])}};
        auto dot=[&](unsigned a){return ((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2];};
        const auto x=dot(0).reload(),y=dot(4).reload(),z=dot(8);
        int32_t index=z.fix();
        if(host_multiplier)
        {
            // Host-only extension uses the linear reciprocal domain and rejects
            // crossing objects. Guest clipping and its clamp paths are unchanged.
            if(index<503 || index>=int32_t(63680*host_multiplier))return false;
        }
        else
        {
            if(path==0x1e3b && index<-4096)index=-4096;
            if(path==0x1e60 && index>63679)index=63679;
            if(index<-4096 || index>63679)return false;
        }
        const auto r=Float::load(reciprocal(index));
        // FIX consumes extended registers here, without a final store/reload.
        const int32_t sx=(x*r+Float::load(origin)).fix(),sy=(Float::integer(200)-y*r).fix();
        if(host_multiplier && (sx<-32768 || sx>32767 || sy<-32768 || sy>32767))return false;
        points.push_back({{uint32_t(sx),uint32_t(sy)}});
    }
    result=std::move(points);return true;
}

template<class Palette> bool quads(const Model &model,const std::vector<Vertex> &points,
    uint32_t extra,uint32_t palette_base,uint32_t texture_base,Palette palette,
    std::vector<Quad> &result)
{
    result.clear();
    if(points.size()!=model.vertices.size() || points.empty() || points.size()>512 ||
        model.polygons.empty() || model.polygons.size()>1024)return false;
    std::vector<Quad> output;
    for(const auto &p:model.polygons)
    {
        const std::array<unsigned,4> offsets={{p[4]&65535,p[4]>>16,p[5]&65535,p[5]>>16}};
        // The guest buffer has THREE words per vertex; this path consumes only XY.
        // The third word is prior buffer data, not this projection's current depth.
        for(auto i:offsets)if(i%3 || i>=3*points.size())return false;
        const auto &a=points[offsets[0]/3],&b=points[offsets[1]/3],&c=points[offsets[2]/3];
        const uint32_t cross=(a[0]-b[0])*(c[1]-b[1])-(a[1]-b[1])*(c[0]-b[0]);
        if(int32_t(cross)>0)continue;
        Quad q{};
        q[0]=uint16_t(p[0]|extra);q[1]=uint16_t(palette_base+palette(p[0]>>16));
        for(unsigned i=0;i<4;++i)
        {q[2+2*i]=uint16_t(points[offsets[i]/3][0]);q[3+2*i]=uint16_t(points[offsets[i]/3][1]);}
        q[10]=uint16_t(p[1]);q[11]=uint16_t(p[1]>>16);
        q[12]=uint16_t(p[2]);q[13]=uint16_t(p[2]>>16);q[14]=uint16_t(p[3]+texture_base);
        output.push_back(q);
    }
    result=std::move(output);return true;
}
} }
