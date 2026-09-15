// SPDX-License-Identifier: BSD-3-Clause
// Recover ordinary future sources during a one-scene frontier counter delay.
#pragma once
#include "offroad_future_sections.h"
#include <algorithm>
#include <set>

namespace cruisn { namespace offroad_future {
// Caller runs at the qualified ordinary scene boundary (PC1bf9), outside an
// allocation. Word6 is the verified section/ordinal identity, preserved after
// activation. Any allocated tag blocks admission, even if its other fields do
// not match: this helper must never produce duplicate live geometry.
template<class Read> bool allocated_tags(Read read,std::set<uint32_t> &result)
{
    result.clear();
    const uint32_t pool=read(0x111ee),slots=1200,stride=22;
    if(pool>0x20000-slots*stride || read(0x111f6)!=0x1b754)return false;
    std::array<bool,1200> free{};uint32_t p=read(0x1b754);
    while(p)
    {
        if(p<pool || p>=pool+slots*stride || (p-pool)%stride)return false;
        const unsigned index=(p-pool)/stride;
        if(free[index])return false;
        free[index]=true;p=read(p);
    }
    std::set<uint32_t> tags;
    for(unsigned i=0;i<slots;++i)if(!free[i])tags.insert(read(pool+i*stride+6));
    result=std::move(tags);return true;
}

// Called AFTER ordinary cached future collection. Never cache pool membership:
// the same frontier can acquire allocations between scene calls. On failure the
// caller's result stays intact. Geometry/material/projection guards still apply.
template<class Read> bool recover_partial(Read read,Result &result)
{
    const auto &f=result.frontier;
    if(f.pretrack || !f.partial || f.front+1>=f.count)return true;
    Frontier actual;if(!frontier(read,actual))return false;
    if(actual.track!=f.track || actual.count!=f.count || actual.current!=f.current ||
        actual.front!=f.front || actual.back!=f.back || actual.partial!=f.partial || actual.pretrack!=f.pretrack)return false;
    std::set<uint32_t> tags;if(!allocated_tags(read,tags))return false;
    const uint32_t number=f.front+1,entry=f.track+4*number,data=read(entry+3);
    if(!rom_span(data,17))return false;
    const uint32_t count=read(data+16);
    if(!count || count>256 || !rom_span(data+17,11*count) || result.sources.size()+count>32768)return false;
    const std::array<uint32_t,3> binding={{read(0x1b4cd),read(0x1b4cf),read(0x1b4ce)}};
    std::vector<Source> extra;
    for(uint32_t ordinal=0;ordinal<count;++ordinal)
    {
        Source s;s.entry=entry;s.source=data+17+11*ordinal;
        std::array<uint32_t,11> words;for(unsigned i=0;i<11;++i)words[i]=read(s.source+i);
        if(!descriptor(words,number,ordinal,count,binding,s))return false;
        if(!s.supported || (s.words[5]&0x200e) || tags.count(s.words[6]))continue;
        if(std::any_of(result.sources.begin(),result.sources.end(),[&](const Source &old){return old.source==s.source;}))return false;
        extra.push_back(s);
    }
    result.sources.insert(result.sources.begin(),extra.begin(),extra.end());
    return true;
}
} }
