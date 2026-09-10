// SPDX-License-Identifier: BSD-3-Clause
// Exotica 2.4 world/translation-only transforms; no CPU execution or game resources.
// Caller supplies the actual rotation source (+5, or +0x8b for special flag0x80).
// Material/matrix-reuse policy and special-model decoding are separate contracts.
#pragma once
#include "scenery_c31.h"
#include <vector>
namespace cruisn { namespace exotica_transform {
using scenery::Float;
struct Prepared
{
    std::array<uint32_t,9> matrix{};
    std::array<uint32_t,3> translation{};
    int32_t depth=0;
};
// Same C31 row-two evaluation as prepare(), without building the other rows
// or rotation matrix. Reload placement matters for extended intermediate bits.
inline bool camera_depth(const std::array<uint32_t,3> &position,
    const std::array<uint32_t,3> &camera,const std::array<uint32_t,9> &view,
    uint32_t flags,int32_t &depth)
{
    depth=0;
    if((flags&3)==3){depth=Float::load(position[2]).fix();return true;}
    if(flags&3)return false;
    std::array<Float,3> delta;
    for(unsigned i=0;i<3;++i)delta[i]=Float::load(position[i])-Float::load(camera[i]);
    const auto z=(delta[1]*Float::load(view[7])+delta[0].reload()*Float::load(view[6]))+
        delta[2].reload()*Float::load(view[8]);
    depth=z.fix();return true;
}
inline bool prepare(const std::array<uint32_t,3> &position,
    const std::array<uint32_t,3> &camera,const std::array<uint32_t,9> &view,
    const std::array<uint32_t,9> &rotation,const std::array<uint32_t,9> &alternate,
    uint32_t flags,Prepared &result)
{
    result=Prepared();if((flags&3)!=0 && (flags&3)!=3)return false;
    std::array<Float,3> delta;std::array<Float,9> m,r;
    for(unsigned i=0;i<3;++i)delta[i]=Float::load(position[i])-Float::load(camera[i]);
    for(unsigned i=0;i<9;++i){m[i]=Float::load(view[i]);r[i]=Float::load(rotation[i]);}
    for(unsigned row=0;row<3;++row)
    {
        const auto x=row?delta[0].reload():delta[0];
        const auto z=(flags&3)==3?Float::load(position[row]):
            (delta[1]*m[row*3+1]+x*m[row*3])+delta[2].reload()*m[row*3+2];
        result.translation[row]=z.store();if(row==2)result.depth=z.fix();
    }
    if(flags&0x80000)result.matrix=alternate;
    else if(flags&2)result.matrix=rotation;
    else for(unsigned row=0;row<3;++row)for(unsigned col=0;col<3;++col)
        result.matrix[row*3+col]=((r[col]*m[row*3]+r[col+3]*m[row*3+1])+r[col+6]*m[row*3+2]).store();
    return true;
}
inline std::vector<uint32_t> packet(const Prepared &prepared,uint32_t scale,bool update)
{
    std::vector<uint32_t> output(1,update?0x07000000:0x16000000);
    const auto f=Float::load(scale);
    if(update)for(auto w:prepared.matrix)output.push_back((Float::load(w)*f).store());
    for(auto w:prepared.translation)output.push_back((Float::load(w)*f).store());
    return output;
}
inline uint32_t select_model(uint32_t descriptor,uint32_t alternate,int32_t depth)
{return alternate && depth>25000?alternate:descriptor;}
inline bool matrix_update(uint32_t flags,uint32_t previous_alpha,uint32_t alpha)
{
    const auto previous=Float::load(previous_alpha),current=Float::load(alpha);
    return !(flags&0x80000 && (previous-Float::integer(254)).e==-128) &&
        ((previous-current).e!=-128 || !(flags&0x10));
}
} }
