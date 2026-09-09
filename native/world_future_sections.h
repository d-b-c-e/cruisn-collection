// license:BSD-3-Clause
// Host-owned World 2.4 section descriptors. No guest allocation or state writes.
#pragma once
#include "world_host_scenery.h"
#include <map>

namespace cruisn { namespace world_future {
using scenery::Float;
using world_host::Descriptor;
template<class Read> bool code_matches(Read read,uint32_t revision=24)
{
    static const uint32_t code[][2]={
        {0x6263,0x08400a02},{0x6265,0x15400010},{0x6266,0x08400a01},{0x6268,0x15400011},
        {0x7b9a,0x084a2501},{0x7b9b,0x6200625c},{0x7ba5,0x0820d57d},{0x7bc7,0x08227c58},
        {0x7bdd,0x08412501},{0x7be5,0x7205dd36},{0x7bef,0x0e200000},{0x7bf0,0x03e0ffec},
        {0x7bf2,0x620094fe},{0x7bf3,0x6a070001},{0x7bf4,0x15400410},{0x7c4e,0x0820d5a3},
        {0x7c6d,0x0840c700},{0x7c81,0x084d0705},{0x7c83,0x08442501},{0x7ca9,0x08400706},
        {0x7cb0,0x08442501},{0x7cc8,0x08400707},{0x7ccf,0x08442501},{0x7cde,0x08412008},
        {0x7ce1,0x0cc02004},{0x90cb,0x24e02122},{0x90db,0xc00201c1},
        {0x9500,0x022a4151},{0x9501,0x0840c200},
        {0xcc35,4263704963U},{0xcc36,4118653474U},{0xcc37,3979254875U},
        {0xcc38,4088417758U},{0xcc39,4178085694U},{0xcc3a,4258616668U},{0xcc3b,4788187U}};
    const auto *profile=world_host::layout(revision);if(!profile)return false;
    static const uint32_t code25[][2]={
        {0x6604,0x08400a02},{0x6606,0x15400010},{0x6607,0x08400a01},{0x6609,0x15400011},
        {0x7b8c,0x084a2501},{0x7b8d,0x620065fd},{0x7b97,0x0820d577},{0x7bb9,0x08227c4a},
        {0x7bcf,0x08412501},{0x7bd7,0x7205dd14},{0x7be1,0x0e200000},{0x7be2,0x03e0ffec},
        {0x7be4,0x620094f3},{0x7be5,0x6a070001},{0x7be6,0x15400410},{0x7c40,0x0820d59d},
        {0x7c5f,0x0840c700},{0x7c73,0x084d0705},{0x7c75,0x08442501},{0x7c9b,0x08400706},
        {0x7ca2,0x08442501},{0x7cba,0x08400707},{0x7cc1,0x08442501},{0x7cd0,0x08412008},
        {0x7cd3,0x0cc02004},{0x90c0,0x24e02122},{0x90d0,0xc00201c1},
        {0x94f5,0x022a4121},{0x94f6,0x0840c200},
        {0x7d1e,0x0820ebdd},{0x7d1f,0x1a600004},{0x7d23,0x04a0d57e}};
    if(revision==24){for(const auto &entry:code)if(read(entry[0])!=entry[1])return false;}
    else {for(const auto &entry:code25)if(read(entry[0])!=entry[1])return false;}
    const uint32_t constants[]={4263704963U,4118653474U,3979254875U,4088417758U,4178085694U,4258616668U,4788187U};
    for(unsigned i=0;i<7;++i)if(read(profile->trig+i)!=constants[i])return false;
    return true;
}
inline bool span(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=65536 && uint64_t(p)+n<=0x1000000;}
inline std::array<uint32_t,9> yaw(Float angle,const std::array<uint32_t,7> &constants)
{
    std::array<Float,7> c;for(int i=0;i<7;++i)c[i]=Float::load(constants[i]);
    const auto half=Float::load(0xff000000),pi_hi=Float::load(0x01490000);
    auto polynomial=[&](Float v){auto square=v*v;auto p=c[2]*square+c[3];
        p=p*square+c[4];p=p*square+c[5];return (p*square)*v+v;};
    bool negative=angle.m<0;auto a=negative?-angle:angle;
    int n=(a*c[0]+half).fix(),sign=negative?-1:1;if(n%2)sign=-sign;
    auto sine=polynomial((a-Float::integer(n)*pi_hi)-Float::integer(n)*c[1])*Float::integer(sign);
    n=((a+c[6])*c[0]+half).fix();auto v=Float::integer(n)-half;
    auto cosine=(polynomial((a-v*pi_hi)-v*c[1])*Float::integer(n%2?-1:1)).store();
    return {{cosine,0x80000000,(-sine).store(),0x80000000,0,0x80000000,sine.store(),0x80000000,cosine}};
}
inline uint32_t object_flags(uint32_t metadata)
{
    uint32_t flags=0x2000|((metadata>>16)&15)|uint32_t(bool(metadata&0xf000));
    switch((metadata>>8)&15){case 3:case 9:flags|=1U<<21;break;case 6:flags|=1U<<31;break;case 7:flags|=1U<<22;break;}
    return flags;
}
struct Source
{
    Descriptor descriptor;
    uint32_t source=0,slot=0,palette_index=0,texture_index=0;
    int32_t override_index=-1;
    bool supported=false;
};
struct Section
{
    uint32_t next=0;
    bool end=false;
    std::vector<Source> sources;
};
struct Stats
{
    uint32_t sections=0,definitions=0,skipped=0,special=0,unbound=0,ready=0,new_sections=0;
    uint32_t stage=0,cursor=0,start=0;
};
struct Cache
{
    std::map<uint32_t,Section> sections;
    uint32_t last_start=0,next_id=0x80000000;
    bool roads=false;
    uint32_t revision=24;
    void clear(){sections.clear();last_start=0;next_id=0x80000000;}
};

template<class Read> bool decode(Read read,uint32_t p,Section &out,uint32_t &next_id,bool roads=false,uint32_t revision=24)
{
    const auto *profile=world_host::layout(revision);if(!profile || (roads && revision!=24))return false;
    if(!span(p,8))return false;
    std::array<uint32_t,12> section{};for(int i=0;i<8;++i)section[i]=read(p+i);
    if(section[0]==UINT32_MAX){out.end=true;out.next=p;return true;}
    const auto extra=(section[0]&8)?4U:0U;
    if(!span(p,8+extra))return false;
    for(uint32_t i=0;i<extra;++i)section[8+i]=read(p+8+i);
    out.next=p+8+extra;
    std::array<uint32_t,7> constants;for(int i=0;i<7;++i)constants[i]=read(profile->trig+i);
    const auto section_yaw=yaw(Float::load(section[4]),constants);
    std::array<Float,9> matrix;for(int i=0;i<9;++i)matrix[i]=Float::load(section_yaw[i]);
    for(uint32_t slot=5;slot<=7;++slot)
    {
        uint32_t block=section[slot];if(!block)continue;
        if(!span(block,2))return false;
        uint32_t count=read(block+1)&65535;
        if(!count || count>4096 || !span(block+2,6*count))return false;
        for(uint32_t index=0;index<count;++index)
        {
            if(out.sources.size()>=8192 || next_id==UINT32_MAX)return false;
            Source source;source.source=block+2+6*index;source.slot=slot;source.descriptor.id=next_id++;
            std::array<uint32_t,6> definition;for(int i=0;i<6;++i)definition[i]=read(source.source+i);
            uint32_t metadata=definition[5],kind=(metadata>>8)&15;
            auto &obj=source.descriptor.words;
            obj[13]=definition[0];obj[14]=object_flags(metadata);obj[15]=metadata&65535;
            // A remains custom allocation. B contributes only checked render
            // fields; the host never initializes or follows its physics links.
            source.supported=kind!=10 && (roads || kind!=11) && !(obj[14]&(roads?0x860:0x861));
            if(roads && kind==11){obj[14]|=1U<<28;obj[15]=(metadata&0xf000)|0x300;}
            if(source.supported)
            {
                if(!span(obj[13]-2,5))return false;
                source.palette_index=read(obj[13]-2);source.texture_index=read(obj[13]-1);
                source.override_index=int32_t(metadata)>>20;
                std::array<Float,3> position;
                for(int i=0;i<3;++i){position[i]=Float::integer(int32_t(definition[1+i])).reload();
                    if(slot!=7 && (section[0]&8))position[i]=(position[i]+Float::load(section[8+i])).reload();}
                std::array<Float,3> transformed={{scenery::dot(position,&matrix[0]).reload(),
                    scenery::dot(position,&matrix[3]).reload(),
                    (position[1]*matrix[7]+(position[2]*matrix[8]+position[0]*matrix[6])).reload()}};
                for(int i=0;i<3;++i)obj[1+i]=(transformed[i]+Float::load(section[1+i])).store();
                auto heading=Float::load(definition[4])+Float::load(section[4]);obj[20]=heading.store();
                const auto object_yaw=yaw(heading,constants);for(int i=0;i<9;++i)obj[4+i]=object_yaw[i];
                obj[27]=p; // Host diagnostic identity only, never written into a guest object.
                if(roads && kind==11)obj[27]|=(1U<<24)|((section[0]&16)?1U<<25:0);
            }
            out.sources.push_back(std::move(source));
        }
    }
    return true;
}

template<class Read> bool collect(Read read,Cache &cache,std::vector<Descriptor> &objects,Stats &stats,uint32_t count=64,bool roads=false,uint32_t revision=24)
{
    const auto *profile=world_host::layout(revision);if(!profile || (roads && revision!=24))return false;
    if(!count || count>128)return false;
    if(cache.roads!=roads || cache.revision!=revision){cache.clear();cache.roads=roads;cache.revision=revision;}
    stats.start=read(profile->section);stats.stage=read(profile->stage);stats.cursor=read(profile->cursor);
    // Before track setup there is no valid section cursor; no host geometry.
    if(!span(stats.start,8)){cache.clear();return true;}
    if(stats.stage>2)return false;
    if(cache.last_start && stats.start<cache.last_start)cache.clear();
    cache.last_start=stats.start;
    // Keep only the frontier and future sections, bounding long-session memory.
    while(!cache.sections.empty() && cache.sections.begin()->first<stats.start)cache.sections.erase(cache.sections.begin());
    uint32_t pt=read(profile->palette),tt=read(profile->texture);
    if(pt>=0x20000 || tt>=0x20000)return false;
    uint32_t p=stats.start;
    for(uint32_t index=0;index<count;++index)
    {
        auto found=cache.sections.find(p);
        if(found==cache.sections.end())
        {
            if(cache.sections.size()>=128)return false;
            Section fresh;if(!decode(read,p,fresh,cache.next_id,roads,revision))return false;
            found=cache.sections.emplace(p,std::move(fresh)).first;++stats.new_sections;
        }
        const auto &section=found->second;if(section.end)break;
        ++stats.sections;
        if(index==0 && stats.stage)
        {
            bool boundary=false;
            for(const auto &source:section.sources)if(source.slot==stats.stage+4)
                boundary|=stats.cursor==source.source || stats.cursor==source.source+6;
            if(!boundary)return false;
        }
        for(const auto &source:section.sources)
        {
            if(index==0 && stats.stage && (source.slot<stats.stage+4 ||
                (source.slot==stats.stage+4 && source.source<stats.cursor))){++stats.skipped;continue;}
            ++stats.definitions;
            if(!source.supported){++stats.special;continue;}
            const uint64_t pa=uint64_t(pt)+source.palette_index,ta=uint64_t(tt)+source.texture_index;
            if(pa>=0x20000 || ta>=0x20000){++stats.unbound;continue;}
            auto obj=source.descriptor;obj.words[16]=read(uint32_t(pa));obj.words[17]=read(uint32_t(ta));
            if(source.override_index>=0)
            {
                const uint64_t address=uint64_t(pt)+uint32_t(source.override_index);
                if(address>=0x20000)return false;
                auto value=read(uint32_t(address));if(int32_t(value)>=0)obj.words[16]=value;
            }
            if(obj.words[16]>65535 || obj.words[17]>65535){++stats.unbound;continue;}
            if(objects.size()>=16384)return false;
            objects.push_back(std::move(obj));++stats.ready;
        }
        p=section.next;
    }
    return true;
}
} }
