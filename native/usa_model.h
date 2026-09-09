// SPDX-License-Identifier: BSD-3-Clause
// USA 4.5's two-word header and interleaved polygon/material model codec.
// Pure host arithmetic: callers own scene selection, residency and safe reads.
#pragma once
#include "scenery_c31.h"
#include "usa_distance.h"
#include <algorithm>
#include <vector>

namespace cruisn { namespace usa_model {
using scenery::Float;
using Quad=std::array<uint16_t,16>;
using Vertex=std::array<uint32_t,3>;
struct Model
{
    uint32_t radius=0;
    std::vector<std::array<uint32_t,2>> vertices;
    std::vector<std::array<uint32_t,5>> polygons;
};
inline bool rom_span(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=8192 && uint64_t(p)+n<=0x1000000;}
inline bool compact_dispatch(uint32_t flags,uint32_t mode,uint32_t enabled)
{
    // LSH -28 at EE tests the outgoing bit27 through C31's LO condition.
    return !(flags&0x08000840) && (mode&15)==4 && enabled!=0;
}
inline uint32_t select_model(const std::array<uint32_t,32> &object,int32_t depth)
{
    uint32_t model=object[13];
    if((object[14]&0x200) && depth>8000)
        model=(object[14]&4) && depth>15000?object[25]:object[24];
    return rom_span(model,2)?model:0;
}

template<class Read> bool load(Read read,uint32_t address,Model &result)
{
    result=Model{};
    if(!rom_span(address,2))return false;
    Model model;model.radius=read(address);
    const uint32_t header=read(address+1);
    const uint32_t vertices=(header&255)+1,polygons=(header>>16)+1;
    if(polygons>1024 || !rom_span(address,2+2*vertices+5*polygons))return false;
    for(uint32_t i=0;i<vertices;++i)
        model.vertices.push_back({{read(address+2+2*i),read(address+3+2*i)}});
    for(uint32_t i=0;i<polygons;++i)
    {
        std::array<uint32_t,5> polygon;
        for(unsigned j=0;j<5;++j)polygon[j]=read(address+2+2*vertices+5*i+j);
        for(unsigned shift=0;shift<32;shift+=8)
            if(((polygon[1]>>shift)&255)>=vertices)return false;
        model.polygons.push_back(polygon);
    }
    result=std::move(model);return true;
}

struct Transform
{
    bool compact=false;
    std::array<uint32_t,9> matrix{};
    std::array<uint32_t,3> center{};
    uint32_t origin_y=Float::integer(200).store();
};
// Ordinary world-space objects only. Scene selection and the game's compact
// dispatch predicate are separate contracts. Alternate local/identity paths
// have not been qualified here and must not silently use the ordinary matrix.
inline bool prepare(const std::array<uint32_t,32> &object,
    const std::array<uint32_t,3> &camera,const std::array<uint32_t,9> &view,
    const std::array<uint32_t,9> &billboard,const std::array<uint32_t,4> &compact_billboard,
    bool compact,uint32_t origin_y,Transform &result)
{
    result=Transform{};
    if(object[14]&0xa3)return false;
    Transform transform;transform.compact=compact;transform.origin_y=origin_y;
    std::array<Float,3> delta;
    std::array<Float,9> matrix;
    for(unsigned i=0;i<3;++i)delta[i]=Float::load(object[1+i])-Float::load(camera[i]);
    for(unsigned i=0;i<9;++i)matrix[i]=Float::load(view[i]);
    for(unsigned i=0;i<3;++i)transform.center[i]=scenery::dot(delta,&matrix[3*i]).store();
    if(object[14]&8)
    {
        if(compact)std::copy(compact_billboard.begin(),compact_billboard.end(),transform.matrix.begin());
        else transform.matrix=billboard;
    }
    else if(compact)
    {
        unsigned i=0;
        for(unsigned a:{0U,6U})for(unsigned b:{0U,2U})
            transform.matrix[i++]=(Float::load(object[4+a])*matrix[b]+
                Float::load(object[6+a])*matrix[6+b]).store();
    }
    else
    {
        for(unsigned row=0;row<3;++row)for(unsigned col=0;col<3;++col)
        {
            const std::array<Float,3> column={{Float::load(object[4+col]),
                Float::load(object[7+col]),Float::load(object[10+col])}};
            transform.matrix[row*3+col]=scenery::dot(column,&matrix[row*3]).store();
        }
    }
    result=transform;return true;
}
// Captured mode reproduces original reciprocal clamps and DMA coordinate wrap
// ONLY for the offline oracle. Host mode rejects near/out-of-range vertices
// and uses a host-generated reciprocal tail; it never reads past guest tables.
enum class Projection { captured,host };
template<class Reciprocal> bool project(const Model &model,const Transform &transform,
    Reciprocal reciprocal,std::vector<Vertex> &result,
    Projection mode=Projection::host,uint32_t far=80000)
{
    result.clear();
    if(!usa_distance::valid_far(far) || model.vertices.empty() || model.vertices.size()>256)return false;
    std::vector<Vertex> projected;
    std::array<Float,9> matrix;
    std::array<Float,3> center;
    for(unsigned i=0;i<9;++i)matrix[i]=Float::load(transform.matrix[i]);
    for(unsigned i=0;i<3;++i)center[i]=Float::load(transform.center[i]);
    for(const auto &vertex:model.vertices)
    {
        const std::array<Float,3> local={{Float::integer(int16_t(vertex[0])),
            Float::integer(int16_t(vertex[0]>>16)),Float::integer(int32_t(vertex[1]))}};
        Float x,y,z;
        if(transform.compact)
        {
            // Preserve the game's product/add order, including center between
            // the two products; reassociation changes C31 rounding.
            x=(local[0]*matrix[0]+center[0])+local[2]*matrix[1];
            y=local[1]+center[1];
            z=(local[0]*matrix[2]+center[2])+local[2]*matrix[3];
        }
        else
        {
            x=scenery::dot(local,&matrix[0]).reload()+center[0];
            y=scenery::dot(local,&matrix[3])+center[1];
            z=scenery::dot(local,&matrix[6])+center[2];
        }
        int32_t index=z.fix()>>4;
        if(mode==Projection::captured)index=std::max(-80,std::min(4999,index));
        else if(z.fix()<1000 || index>int32_t(usa_distance::maximum_index(far)))return false;
        const Float r=Float::load(index<5000?reciprocal(index):usa_distance::cached_reciprocal(uint32_t(index),far));
        const Float sx=(x*r+Float::integer(256)).reload();
        const Float sy=((y*r)*Float::load(0x00052000)+Float::load(transform.origin_y)).reload();
        if(mode==Projection::host && (sx.fix()<-32768 || sx.fix()>32767 || sy.fix()<-32768 || sy.fix()>32767))return false;
        projected.push_back({{sx.store(),sy.store(),z.store()}});
    }
    result=std::move(projected);return true;
}

// Lookup receives the original polygon flags. It must use a checked palette
// table; direct=true instead uses object word16. No World texture offset exists.
template<class Palette> bool quads(const Model &model,const std::vector<Vertex> &projected,
    bool direct,Palette palette,std::vector<Quad> &result)
{
    result.clear();
    if(projected.size()!=model.vertices.size() || projected.empty() || model.polygons.size()>1024)return false;
    std::vector<Quad> output;
    for(const auto &polygon:model.polygons)
    {
        std::array<unsigned,4> indices;
        for(unsigned j=0;j<4;++j)
        {
            indices[j]=(polygon[1]>>(8*j))&255;
            if(indices[j]>=projected.size())return false;
        }
        std::array<std::array<Float,2>,4> p;
        for(unsigned j=0;j<4;++j)for(unsigned k=0;k<2;++k)p[j][k]=Float::load(projected[indices[j]][k]);
        const auto &a=p[0],&b=p[1],&c=p[2];
        const Float cross=(b[1]-c[1])*(b[0]-a[0])-(b[0]-c[0])*(b[1]-a[1]);
        // USA retains zero-area polygons in this path; World does not.
        if(cross.e!=-128 && cross.m>=0)continue;
        Quad q{};q[0]=uint16_t(polygon[0]);
        const uint32_t material=palette(polygon[0]);
        q[1]=uint16_t(direct?material:(material>>16)<<8);
        for(unsigned j=0;j<4;++j){q[2+2*j]=uint16_t(p[j][0].fix());q[3+2*j]=uint16_t(p[j][1].fix());}
        q[10]=uint16_t(polygon[2]);q[11]=uint16_t(polygon[2]>>16);
        q[12]=uint16_t(polygon[3]);q[13]=uint16_t(polygon[3]>>16);
        q[14]=uint16_t(polygon[4]);output.push_back(q);
    }
    result=std::move(output);return true;
}
} }
