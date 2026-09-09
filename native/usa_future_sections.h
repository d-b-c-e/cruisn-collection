// SPDX-License-Identifier: BSD-3-Clause
// USA 4.5 host-owned section descriptors. No guest allocation or state writes.
#pragma once
#include "usa_model.h"
#include "usa_host_scenery.h"
#include "world_future_sections.h" // Shared, independently checked C31 yaw polynomial only.

namespace cruisn { namespace usa_future {
using scenery::Float;
struct Source
{
    uint32_t section=0,source=0,stage=0,number=0,prefix=0,binding=0;
    bool supported=false,resident=false;
    std::array<uint32_t,34> words{};
};
struct Result
{
    uint32_t start=0,loading=0,number=0;
    bool partial=false,pretrack=false,end=false;
    std::vector<Source> sources;
};
inline bool span(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=65536 && uint64_t(p)+n<=0x1000000;}
inline uint32_t header_size(uint32_t flags)
{return 6+uint32_t(bool(flags&1))+((flags&8)?4:0)+uint32_t(bool(flags&0x1000));}
template<class Read> bool code_matches(Read read)
{
    const uint32_t code[][2]={{0x401a,0x0828e49d},{0x403b,0x1528e49d},
        {0x4096,0x082ae4a5},{0x40a1,0x152ae4a5},{0x40b9,0x62007035},
        {0x4114,0x0840040f},{0x95f7,0x6200b072},{0x9efc,0x0840c200},
        {0x9efd,0x6a050005},{0x9f45,0x10628000},{0x9f46,0x15420801},
        {0x9ec4,0x0820cc3f},{0x9ec6,0x1520cc41},{0x9edb,0x08422101},
        {0x9ee9,0xda822221},{0x9fb7,0x1528cc3f},{0x9fc3,0x1541c100}};
    for(const auto &op:code)if(read(op[0])!=op[1])return false;
    const uint32_t constants[]={4263704963U,4118653474U,3979254875U,4088417758U,4178085694U,4258616668U,4788187U};
    for(unsigned i=0;i<7;++i)if(read(0xc8ed+i)!=constants[i])return false;
    return true;
}
inline uint32_t flags(uint32_t prefix,uint32_t metadata)
{
    uint32_t out=((metadata>>16)&0x3b)|((prefix&0x2000)?0x400:0)|
        ((prefix&0x1000)?0x40:0)|((metadata&0x1000)?(1U<<26):0);
    switch((metadata>>8)&15){case 3:case 11:out|=1U<<28;break;case 9:out|=1U<<21;break;case 6:out|=1U<<31;break;}
    return out;
}
inline bool descriptor(const std::array<uint32_t,6> &definition,
    const std::array<uint32_t,12> &section,uint32_t effective_flags,uint32_t heading,
    const std::array<uint32_t,7> &constants,Source &out)
{
    const uint32_t metadata=definition[5];
    out.words={};out.supported=false;out.resident=false;
    if(metadata&0x2000)return true; // Custom allocator not yet mapped.
    if(!span(definition[0]-1,3) || out.number>0xffffff)return false;
    auto &obj=out.words;
    obj[13]=definition[0];obj[14]=flags(out.prefix,metadata)|0x2000;
    obj[15]=((metadata>>8)&15)==11?0x300:(metadata&0xfff);
    obj[31]=(out.number<<8)|0xaa;
    if(((metadata>>8)&15)==11)
        obj[30]=(out.number<<8)|((effective_flags&8)?255-(metadata&255):(metadata&255));
    obj[16]=(out.binding>>16)<<8;
    const auto section_yaw=world_future::yaw(Float::load(heading),constants);
    std::array<Float,9> matrix;for(unsigned i=0;i<9;++i)matrix[i]=Float::load(section_yaw[i]);
    std::array<Float,3> position;
    for(unsigned i=0;i<3;++i)
    {
        position[i]=Float::integer(int32_t(definition[1+i])).reload();
        if(effective_flags&8)
            position[i]=(position[i]+Float::load(section[6+uint32_t(bool(section[0]&1))+i])).reload();
    }
    const std::array<Float,3> transformed={{scenery::dot(position,&matrix[0]).reload(),
        scenery::dot(position,&matrix[3]).reload(),
        (position[1]*matrix[7]+(position[2]*matrix[8]+position[0]*matrix[6])).reload()}};
    for(unsigned i=0;i<3;++i)obj[1+i]=(transformed[i]+Float::load(section[1+i])).store();
    const auto angle=Float::load(definition[4])+Float::load(heading);
    obj[21]=angle.store();const auto yaw=world_future::yaw(angle,constants);
    std::copy(yaw.begin(),yaw.end(),obj.begin()+4);
    out.supported=!(obj[14]&0x8e3);
    out.resident=out.binding!=0; // Palette reference only; texture lifetime is separate.
    return true;
}
template<class Read> bool decode(Read read,uint32_t p,uint32_t number,
    std::vector<Source> &result,uint32_t &next,bool bindings=true)
{
    result.clear();next=0;
    if(!span(p,12))return false;
    std::array<uint32_t,12> section;for(unsigned i=0;i<12;++i)section[i]=read(p+i);
    if(section[0]==UINT32_MAX){next=p;return true;}
    const uint32_t count=header_size(section[0]);next=p+count;
    std::array<uint32_t,7> constants;for(unsigned i=0;i<7;++i)constants[i]=read(0xc8ed+i);
    const uint32_t table=bindings?read(0x9ea9):0,owners=bindings?read(0x9ea8):0;
    if(bindings && (table>=0x20000 || uint64_t(owners)+128>0x20000))return false;
    std::vector<Source> objects;
    for(uint32_t stage=0;stage<3;++stage)
    {
        if((stage==1 && !(section[0]&1)) || (stage==2 && !(section[0]&0x1000)))continue;
        const uint32_t slot=stage==0?5:stage==1?6:count-1;
        const uint32_t block=section[slot];if(!span(block,2))return false;
        const uint32_t entries=read(block+1);
        if(!entries || entries>4096 || !span(block+2,6*entries))return false;
        const uint32_t heading=(stage==2 && (section[0]&8))?section[9+uint32_t(bool(section[0]&1))]:section[4];
        for(uint32_t index=0;index<entries;++index)
        {
            if(objects.size()>=12288)return false;
            Source object;object.section=p;object.source=block+2+6*index;object.stage=stage;object.number=number;
            std::array<uint32_t,6> definition;for(unsigned i=0;i<6;++i)definition[i]=read(object.source+i);
            // Custom handlers can have a non-model first operand. Never follow it.
            if(!(definition[5]&0x2000))
            {
                if(!span(definition[0]-1,3))return false;
                object.prefix=read(definition[0]-1);const uint32_t binding=table+(object.prefix&0xfff);
                if(bindings && binding>=0x20000)return false;
                object.binding=bindings?read(binding):0;
                if(bindings && object.binding)
                {
                    const uint32_t slot=object.binding>>16;
                    if(slot>=128 || !(object.binding&65535) ||
                       read(owners+slot)!=(0x8000|(object.prefix&0xfff)))return false;
                }
            }
            if(!descriptor(definition,section,stage==2?section[0]&~8U:section[0],heading,constants,object))return false;
            objects.push_back(object);
        }
    }
    result=std::move(objects);return true;
}
template<class Read> bool build(Read read,Result &result,uint32_t limit=64)
{
    result=Result{};
    if(!limit || limit>128)return false;
    Result out;out.start=read(0xe4a5);out.loading=read(0xe49d);out.number=read(0xe4a4);
    const uint32_t track=read(0xa12e);
    if(!out.start && !out.loading){out.pretrack=true;result=std::move(out);return true;}
    if(!span(out.start,1) || !span(out.loading,1) || !span(track,1) || out.number>4096)return false;
    uint32_t p=track,previous=0;
    for(uint32_t i=0;i<out.number;++i)
    {
        if(!span(p,1) || read(p)==UINT32_MAX)return false;
        previous=p;p+=header_size(read(p));
    }
    if(p!=out.start || (out.loading!=out.start && out.loading!=previous))return false;
    out.partial=out.loading!=out.start;
    for(uint32_t i=0;i<limit;++i)
    {
        if(!span(p,1))return false;
        if(read(p)==UINT32_MAX){out.end=true;break;}
        std::vector<Source> sources;uint32_t following;
        if(!decode(read,p,out.number+i+1,sources,following) || out.sources.size()+sources.size()>65536)return false;
        out.sources.insert(out.sources.end(),sources.begin(),sources.end());p=following;
    }
    result=std::move(out);return true;
}

struct Uploads
{
    uint32_t count=0;
    bool textures=false;
    std::array<bool,128> palettes{};
};
template<class Read> bool queued_uploads(Read read,Uploads &result)
{
    result=Uploads{};Uploads uploads;std::set<uint32_t> seen;
    uint32_t p=read(0xcc3f);
    while(p)
    {
        if(p<0xcc42 || p>=0xce42 || (p-0xcc42)%4 || !seen.insert(p).second || seen.size()>128)return false;
        const uint32_t destination=read(p+2),length=read(p+3)&0x7fffffff;
        if(!length || length>0x200000)return false;
        const uint64_t end=uint64_t(destination)+length;
        if(destination>=0x9e0000 && end<=0x9e8000)
        {
            for(uint32_t bank=(destination-0x9e0000)/256;bank<=(uint32_t(end)-1-0x9e0000)/256;++bank)
                uploads.palettes[bank]=true;
        }
        else if(destination>=0xa00000 && end<=0xc00000)uploads.textures=true;
        else return false; // Unmapped upload target must not be treated as ready.
        ++uploads.count;p=read(p);
    }
    result=uploads;return true;
}
struct Section
{
    uint32_t next=0,number=0;
    std::vector<Source> sources;
};
struct Cache
{
    uint32_t track=0,last=0;
    std::map<uint32_t,Section> sections;
    std::map<uint32_t,std::vector<uint32_t>> palettes;
    void clear(){track=last=0;sections.clear();palettes.clear();}
};
struct Stats
{
    uint32_t start=0,loading=0,number=0,sections=0,new_sections=0,definitions=0;
    uint32_t special=0,unbound=0,deferred=0,ready=0,uploads=0;
    bool partial=false,pretrack=false;
};
template<class Read> bool collect(Read read,Cache &cache,std::vector<usa_host::Descriptor> &result,
    Stats &stats,uint32_t limit=64)
{
    result.clear();stats=Stats{};
    if(!limit || limit>128)return false;
    Stats current;current.start=read(0xe4a5);current.loading=read(0xe49d);current.number=read(0xe4a4);
    const uint32_t track=read(0xa12e);
    if(!current.start && !current.loading){cache.clear();current.pretrack=true;stats=current;return true;}
    if(!span(track,1) || !span(current.start,1) || !span(current.loading,1) || current.number>4096)return false;
    uint32_t p=track,previous=0;
    for(uint32_t i=0;i<current.number;++i)
    {
        if(!span(p,1) || read(p)==UINT32_MAX)return false;
        previous=p;p+=header_size(read(p));
    }
    if(p!=current.start || (current.loading!=current.start && current.loading!=previous))return false;
    current.partial=current.loading!=current.start;
    if(cache.track!=track || (cache.last && current.start<cache.last))cache.clear();
    cache.track=track;cache.last=current.start;
    while(!cache.sections.empty() && cache.sections.begin()->first<current.start)cache.sections.erase(cache.sections.begin());
    // Static palette-index lists are small, but remain bounded on long sessions.
    if(cache.palettes.size()>4096)cache.palettes.clear();
    const uint32_t table=read(0x9ea9),owners=read(0x9ea8);
    if(table>=0x20000 || uint64_t(owners)+128>0x20000 || read(0x62)!=table)return false;
    Uploads uploads;if(!queued_uploads(read,uploads))return false;current.uploads=uploads.count;
    std::vector<usa_host::Descriptor> objects;
    std::set<uint32_t> live_sections;
    p=current.start;
    for(uint32_t number=0;number<limit;++number)
    {
        if(!span(p,1))return false;
        if(read(p)==UINT32_MAX)break;
        auto found=cache.sections.find(p);
        if(found==cache.sections.end())
        {
            if(cache.sections.size()>=128)return false;
            Section section;section.number=current.number+number+1;
            if(!decode(read,p,section.number,section.sources,section.next,false))return false;
            found=cache.sections.emplace(p,std::move(section)).first;++current.new_sections;
        }
        const auto &section=found->second;
        if(section.number!=current.number+number+1)return false;
        ++current.sections;live_sections.insert(p);
        for(size_t ordinal=0;ordinal<section.sources.size();++ordinal)
        {
            const auto &source=section.sources[ordinal];++current.definitions;
            if(!source.supported){++current.special;continue;}
            const uint32_t model=source.words[13];auto material=cache.palettes.find(model);
            if(material==cache.palettes.end())
            {
                if(cache.palettes.size()>=8192)return false;
                std::set<uint32_t> indices;indices.insert(source.prefix&0xfff);
                if(!(source.words[14]&0x400))
                {
                    usa_model::Model decoded;if(!usa_model::load(read,model,decoded))return false;
                    for(const auto &polygon:decoded.polygons)indices.insert(polygon[0]>>16);
                }
                material=cache.palettes.emplace(model,std::vector<uint32_t>(indices.begin(),indices.end())).first;
            }
            bool unbound=false,deferred=uploads.textures;uint32_t direct=0;
            for(uint32_t index:material->second)
            {
                if(index>=4096 || uint64_t(table)+index>=0x20000)return false;
                const uint32_t binding=read(table+index),slot=binding>>16;
                if(!binding){unbound=true;continue;}
                // A pending guest release/upload may temporarily clear the refcount.
                // Skip this descriptor instead of borrowing a recycled bank.
                if(slot>=128 || !(binding&65535) || read(owners+slot)!=(0x8000|index))
                {unbound=true;continue;}
                deferred|=uploads.palettes[slot];
                if(index==(source.prefix&0xfff))direct=slot<<8;
            }
            if(unbound){++current.unbound;continue;}
            if(deferred){++current.deferred;continue;}
            if(objects.size()>=16384 || ordinal>=65536 || section.number>=32768)return false;
            usa_host::Descriptor object;object.id=0x80000000|(section.number<<16)|uint32_t(ordinal);
            std::copy_n(source.words.begin(),32,object.words.begin());object.words[16]=direct;
            objects.push_back(object);++current.ready;
        }
        p=section.next;
    }
    for(auto it=cache.sections.begin();it!=cache.sections.end();)
        if(!live_sections.count(it->first))it=cache.sections.erase(it);else ++it;
    result=std::move(objects);stats=current;return true;
}
} }
