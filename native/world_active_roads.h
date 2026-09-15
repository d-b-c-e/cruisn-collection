// license:BSD-3-Clause
// Fresh active-list membership for private, wholly-margin road recovery.
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
template<class Read> bool collect(Read read,std::vector<world_host::Descriptor> &out,uint32_t revision)
{
    if(!code_matches(read,revision))return false;
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
            // 0x3020). Valid topology does not make those ordinary active roads.
            // Exclude them without aborting a scene or granting draw permission.
            if((d.words[14]&0x3861)!=0x1001 || d.words[16]>65535 || d.words[17]>65535)continue;
            result.push_back(d);
        }
    }
    out.insert(out.end(),result.begin(),result.end());return true;
}
} }
