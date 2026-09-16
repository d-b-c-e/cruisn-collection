// SPDX-License-Identifier: BSD-3-Clause
// Standalone original bit4/four-vertex billboard arithmetic. No future admission,
// material, damage-state, clipping, basis ownership or GPU command acceptance.
#pragma once
#include "scenery_c31.h"

namespace cruisn { namespace offroad_billboard {
using scenery::Float;
inline bool prepare(const std::array<uint32_t,22> &object,
    const std::array<uint32_t,12> &view,const std::array<uint32_t,12> &basis,
    std::array<uint32_t,12> &result)
{
    result={};if((object[5]&6)!=4)return false;
    std::array<uint32_t,12> output{};
    std::array<Float,12> m;for(unsigned i=0;i<12;++i)m[i]=Float::load(view[i]);
    const std::array<Float,3> v={{Float::load(object[11]),Float::load(object[12]),Float::load(object[13])}};
    for(unsigned a:{0U,4U,8U}) {
        output[a+3]=(((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2]).store();
        for(unsigned i=0;i<3;++i)output[a+i]=basis[a+i];
    }
    result=output;return true;
}

template<class Reciprocal> bool project(const std::array<uint32_t,12> &vertices,
    const std::array<uint32_t,12> &matrix,uint32_t origin,Reciprocal reciprocal,
    std::array<uint32_t,12> &result)
{
    result={};std::array<uint32_t,12> output{};
    std::array<Float,12> m;for(unsigned i=0;i<12;++i)m[i]=Float::load(matrix[i]);
    for(unsigned offset=0;offset<12;offset+=3) {
        const std::array<Float,3> v={{Float::load(vertices[offset]),Float::load(vertices[offset+1]),Float::load(vertices[offset+2])}};
        const auto coordinate=[&](unsigned a){return ((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2];};
        const auto x=coordinate(0),y=coordinate(4),z=coordinate(8);const auto depth=z.fix();
        if(depth<0 || depth>63679)return false;
        const auto r=Float::load(reciprocal(uint32_t(depth)));
        output[offset]=uint32_t((x.reload()*r+Float::load(origin)).fix());
        output[offset+1]=uint32_t((Float::integer(200)-y.reload()*r).fix());
        output[offset+2]=uint32_t(depth);
    }
    result=output;return true;
}

inline bool quad(const std::array<uint32_t,22> &object,const std::array<uint32_t,6> &polygon,
    const std::array<uint32_t,12> &projected,uint32_t palette_lookup,uint32_t extra_flags,
    std::array<uint16_t,16> &result)
{
    result={};if((object[5]&6)!=4 || (extra_flags && extra_flags!=0x2000))return false;
    const std::array<uint32_t,4> offsets={{polygon[4]&65535,polygon[4]>>16,polygon[5]&65535,polygon[5]>>16}};
    for(auto i:offsets)if(i%3 || i>=12)return false;
    std::array<uint16_t,16> output{};
    output[0]=uint16_t(polygon[0]|extra_flags);output[1]=uint16_t(object[18]+palette_lookup);
    for(unsigned i=0;i<4;++i)for(unsigned k=0;k<2;++k)output[2+2*i+k]=uint16_t(projected[offsets[i]+k]);
    output[10]=uint16_t(polygon[1]);output[11]=uint16_t(polygon[1]>>16);
    output[12]=uint16_t(polygon[2]);output[13]=uint16_t(polygon[2]>>16);
    output[14]=uint16_t(polygon[3]+object[19]);result=output;return true;
}
} }
