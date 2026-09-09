// SPDX-License-Identifier: BSD-3-Clause
// Off Road 1.63 ordinary object transforms and LOD selection. No CPU execution.
// Table callbacks serve bounded ROM operands at indices -1..16384; callers own
// revision, material and scene guards. Alternate local/billboard paths fail.
#pragma once
#include "scenery_c31.h"
#include <vector>
#include <utility>
namespace cruisn { namespace offroad_transform {
using scenery::Float;
// The original interpolator returns extended sine and stores/reloads cosine.
template<class Table> std::pair<Float,Float> trig(uint32_t angle,Table table)
{
    const auto fraction=Float::integer(int32_t(angle&0x1ffff))*Float::load(0xef000040);
    const int32_t shift=int32_t(angle<<1)>>17,i=shift<0?-shift:shift,j=16383-i;
    const auto s=Float::load(table(i)),c=Float::load(table(j));
    if(!(angle&0x80000000))
    {
        if(shift>=0)return {s+(Float::load(table(i+1))-s)*fraction,
            (c+(Float::load(table(j-1))-c)*fraction).reload()};
        return {s+(Float::load(table(i-1))-s)*fraction,
            ((c-Float::load(table(j+1)))*fraction-c).reload()};
    }
    if(shift>=0)return {(s-Float::load(table(i+1)))*fraction-s,
        ((c-Float::load(table(j-1)))*fraction-c).reload()};
    return {(s-Float::load(table(i-1)))*fraction-s,
        (c+(Float::load(table(j+1))-c)*fraction).reload()};
}
template<class Table> bool prepare(const std::array<uint32_t,22> &object,
    const std::array<uint32_t,12> &view,Table table,std::array<uint32_t,12> &result)
{
    result={};const auto flags=object[5];if(flags&0x200e)return false;
    std::array<Float,12> m;for(unsigned i=0;i<12;++i)m[i]=Float::load(view[i]);
    const std::array<Float,3> v={{Float::load(object[11]),Float::load(object[12]),Float::load(object[13])}};
    std::array<uint32_t,12> output{};
    for(unsigned a:{0U,4U,8U})output[a+3]=(((v[0]*m[a]+m[a+3])+v[1]*m[a+1])+v[2]*m[a+2]).store();
    if(flags&1)
    {
        for(unsigned a:{0U,1U,2U,4U,5U,6U,8U,9U,10U})output[a]=view[a];
    }
    else if(flags&0x10)
    {
        const auto sc=trig(object[15],table);const auto s=sc.first,c=sc.second;
        for(unsigned a:{0U,4U,8U})
        {
            output[a]=((-s)*m[a+2]+c*m[a]).store();output[a+1]=view[a+1];
            // The game temporarily stores this product in its matrix buffer.
            output[a+2]=(s*m[a]+(c*m[a+2]).reload()).store();
        }
    }
    else
    {
        const auto x=trig(object[14],table),y=trig(object[15],table),z=trig(object[16],table);
        const auto sx=x.first,cx=x.second,sy=y.first,cy=y.second,sz=z.first,cz=z.second;
        const auto a=(cy*sx)*sz-cz*sy,b=(sy*sx).reload(),c=cy*cz+(sy*sx)*sz;
        const auto d=(cy*sz-cz*b).reload(),e=(cy*sx)*cz+sy*sz;
        for(unsigned i:{0U,4U,8U})
        {
            output[i]=((m[i]*c-(cx*m[i+1])*sz)+m[i+2]*a).store();
            output[i+1]=((m[i]*d+(cx*m[i+1])*cz)-m[i+2]*e).store();
            output[i+2]=(((m[i]*sy)*cx+m[i+1]*sx)+(m[i+2]*cy)*cx).store();
        }
    }
    result=output;return true;
}
inline std::pair<unsigned,int32_t> select_lod(const std::array<uint32_t,22> &object,
    const std::array<uint32_t,13> &context)
{
    const auto flags=object[5];if(!(flags&0x20) || context[1]!=context[2])return {0,0};
    const int32_t delta=int32_t(object[8]-context[0]);uint32_t adjustment=0;
    if(delta>int32_t(context[5]))adjustment=context[4];
    if(delta<=int32_t(context[6]))adjustment=context[3];
    const int32_t relative=int32_t(uint32_t(delta)+adjustment);
    const unsigned pair=(flags&0x2000)?4:(flags&0x80)?2:0;
    unsigned index=relative>=int32_t(context[7+pair])?1:0;
    if(index && (flags&0x2040) && relative>=int32_t(context[8+pair]))index=2;
    return {index,relative};
}
} }
