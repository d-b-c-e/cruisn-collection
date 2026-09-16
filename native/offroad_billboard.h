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
} }
