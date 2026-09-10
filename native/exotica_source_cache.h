// SPDX-License-Identifier: BSD-3-Clause
// Cached immutable-ROM descriptors with current RAM bindings and loader frontier.
#pragma once
#include "exotica_future_sections.h"
#include <map>

namespace cruisn { namespace exotica_future {
// Compare declared fields, never structure padding or a lossy fingerprint.
inline bool equal_sources(const Result &a,const Result &b)
{
    if(a.pretrack!=b.pretrack || a.partial!=b.partial || a.frontier!=b.frontier ||
        a.sources.size()!=b.sources.size() || a.sections.size()!=b.sections.size())return false;
    for(size_t i=0;i<a.sources.size();++i)
    {
        const auto &x=a.sources[i],&y=b.sources[i];
        if(x.entry!=y.entry || x.source!=y.source || x.index!=y.index || x.ordinal!=y.ordinal ||
            x.supported!=y.supported || x.future!=y.future || x.words!=y.words)return false;
    }
    for(size_t i=0;i<a.sections.size();++i)
    {
        const auto &x=a.sections[i],&y=b.sections[i];
        if(x.entry!=y.entry || x.index!=y.index || x.cursor!=y.cursor || x.heading!=y.heading ||
            x.section_heading!=y.section_heading || x.gap!=y.gap || x.flags!=y.flags ||
            x.position!=y.position || x.matrix!=y.matrix || x.header!=y.header || x.initial!=y.initial)return false;
    }
    return true;
}

class CachedSources
{
    Result track_;
    Section terminal_;
    std::map<uint32_t,uint32_t> dependencies_;
    uint64_t owner_=0;
    bool valid_=false;
    static bool frontier_word(uint32_t p)
    {return p==0x590 || p==0x597 || (p>=0x598 && p<=0x59c);}
public:
    uint64_t hits=0,misses=0;
    void invalidate() {valid_=false;}

    // A nonzero owner identifies one immutable main/banked ROM mapping for the
    // lifetime of this cache. Change it or invalidate BEFORE modifying ROM.
    // Every RAM operand read by the full builder remains checked on every call.
    // WaveRAM models and current texture/palette colors are outside this cache.
    template<class Read>
    bool build(Read read,uint64_t owner,Result &result,bool partial=false)
    {
        result=Result();
        if(!owner)return false;
        const auto entry=read(0x597),number=read(0x590),cursor=read(0x598);
        if(!entry && !number && !cursor)
        {
            invalidate();
            const bool ok=exotica_future::build(read,result,partial);
            if(ok)++misses;
            return ok;
        }
        bool hit=valid_ && owner_==owner;
        if(hit)for(const auto &dependency:dependencies_)
            if(read(dependency.first)!=dependency.second){hit=false;break;}
        if(!hit)
        {
            std::map<uint32_t,uint32_t> dependencies;
            auto tracked=[&](uint32_t p){
                const auto value=read(p);
                if(p<0x40000 && !frontier_word(p))dependencies[p]=value;
                return value;
            };
            Result track;
            if(!exotica_future::build(tracked,track,partial) || track.sections.empty())return false;
            const auto &last=track.sections.back();Section terminal;
            terminal.entry=last.entry+4;terminal.index=last.index+1;
            terminal.cursor=last.cursor+last.gap+1;
            std::array<Float,3> delta;
            for(unsigned i=0;i<3;++i)
            {delta[i]=Float::load(last.header[i]);if(last.flags&1)delta[i]=-delta[i];}
            const auto advance=transform(delta,last.matrix);
            for(unsigned i=0;i<3;++i)
                terminal.position[i]=(advance[i]+Float::load(last.position[i])).store();
            terminal.heading=((last.flags&1)?Float::load(last.heading)-Float::load(last.header[3]):
                Float::load(last.header[3])+Float::load(last.heading)).store();
            track_=std::move(track);terminal_=terminal;dependencies_=std::move(dependencies);
            owner_=owner;valid_=true;
        }
        const Section *frontier=nullptr;
        for(const auto &section:track_.sections)if(section.entry==entry){frontier=&section;break;}
        if(!frontier && !partial && terminal_.entry==entry)frontier=&terminal_;
        if(!frontier || frontier->cursor!=cursor || frontier->index*256!=number ||
            frontier->heading!=read(0x59c))return false;
        for(unsigned i=0;i<3;++i)if(frontier->position[i]!=read(0x599+i))return false;
        result=track_;result.frontier=entry;result.partial=partial;
        for(auto &source:result.sources)
            source.future=uint64_t(source.entry)>=uint64_t(entry)+4*partial;
        if(hit)++hits;else ++misses;
        return true;
    }
};
} }
