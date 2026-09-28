// license:BSD-3-Clause
// Fresh active-list membership for private, wholly-margin road/scenery recovery.
#pragma once
#include "world_host_scenery.h"
#include <set>
namespace cruisn { namespace world_active_roads {
inline std::array<uint32_t,4> heads(uint32_t revision)
{
    return revision==24 ? std::array<uint32_t,4>{{0x61ee,0x61eb,0x61ed,0x61ef}} :
        std::array<uint32_t,4>{{0x658f,0x658c,0x658e,0x6590}};
}
template<class Read> bool code_matches(Read read,uint32_t revision)
{
    if(revision!=24 && revision!=25)return false;
    const auto globals=heads(revision);
    const uint32_t pcs[]={0x69,0x6c,0x6f,0x72};
    for(unsigned i=0;i<4;++i)
        if(read(pcs[i])!=(0x08280000|globals[i]) || read(pcs[i]+1)!=0x6200034c)return false;
    return true;
}
template<class Read> bool collect(Read read,std::vector<world_host::Descriptor> &out,uint32_t revision,
                                  bool include_nonroads=false)
{
    if(!code_matches(read,revision))return false;
    std::array<world_host::Float,3> camera{};
    std::array<world_host::Float,9> view{};
    world_host::Float ox{};
    uint32_t table=0;
    if(include_nonroads)
    {
        const uint32_t cam=read(0x41),matrix=read(0x43),origin=read(0x47)+2;
        table=read(0x4d);
        const auto *layout=world_host::layout(revision);
        if(!layout || cam>=0x20000-3 || matrix<0x809800 || matrix>0x809ff7 ||
           origin<0x809800 || origin>0x809ffe || table!=layout->table)return false;
        for(unsigned i=0;i<3;++i)camera[i]=world_host::Float::load(read(cam+i));
        for(unsigned i=0;i<9;++i)view[i]=world_host::Float::load(read(matrix+i));
        ox=world_host::Float::load(read(origin));
    }
    std::vector<world_host::Descriptor> result;
    std::set<uint32_t> seen;
    for(auto global:heads(revision))
    {
        uint32_t head=read(global);
        if(head<0x1000 || head>=0x20000)return false;
        uint32_t p=read(head);
        while(p)
        {
            if(p<0x1000 || p>0x20000-32 || seen.size()>=2048 || !seen.insert(p).second)return false;
            world_host::Descriptor d;d.id=0xc0000000|p;d.active_margin=true;
            for(unsigned i=0;i<32;++i)d.words[i]=read(p+i);
            p=d.words[0];
            // The renderer also traverses menu/effect objects (e.g. captured
            // 0x3020). A separate opt-in admits only ordinary 0x1000 non-roads;
            // original active-road experiments keep their exact old membership.
            const uint32_t klass=d.words[14]&0x3861;
            if((klass!=0x1001 && !(include_nonroads && klass==0x1000)) ||
               d.words[16]>65535 || d.words[17]>65535)continue;
            if(klass==0x1000)
            {
                // This first non-road trial admits static, horizontally culled
                // objects only. Alternate-LOD/dynamic models need their own
                // source-time proof; none is required by the recorded NY gap.
                if(d.words[14]&0x200 || !world_host::pointer(d.words[13],3))continue;
                std::array<world_host::Float,3> delta,center;
                for(unsigned i=0;i<3;++i)delta[i]=world_host::Float::load(d.words[i+1])-camera[i];
                for(unsigned i=0;i<3;++i)center[i]=world_host::dot(delta,&view[i*3]);
                const int32_t depth=center[2].fix();
                const uint32_t radius=read(d.words[13]);
                if(depth<=0 || depth>=80000 || radius>uint32_t(INT32_MAX))continue;
                const auto r=world_host::Float::load(read(table+uint32_t(std::min(4999,depth>>4))));
                const auto extent=world_host::Float::integer(int32_t(radius))*r;
                const auto left=center[0]*r+extent+ox;
                const auto right=(left-extent-extent)-world_host::Float::integer(512);
                if(!(left.e!=-128 && left.m<0) && !(right.e!=-128 && right.m>=0))continue;
            }
            result.push_back(d);
        }
    }
    out.insert(out.end(),result.begin(),result.end());return true;
}
} }
