// SPDX-License-Identifier: BSD-3-Clause
// USA 4.5 host-owned section descriptors. No guest allocation or state writes.
#pragma once
#include "usa_model.h"
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
        {0x9efd,0x6a050005},{0x9f45,0x10628000},{0x9f46,0x15420801}};
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
    std::vector<Source> &result,uint32_t &next)
{
    result.clear();next=0;
    if(!span(p,12))return false;
    std::array<uint32_t,12> section;for(unsigned i=0;i<12;++i)section[i]=read(p+i);
    if(section[0]==UINT32_MAX){next=p;return true;}
    const uint32_t count=header_size(section[0]);next=p+count;
    std::array<uint32_t,7> constants;for(unsigned i=0;i<7;++i)constants[i]=read(0xc8ed+i);
    const uint32_t table=read(0x9ea9),owners=read(0x9ea8);
    if(table>=0x20000 || uint64_t(owners)+128>0x20000)return false;
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
                if(binding>=0x20000)return false;
                object.binding=read(binding);
                if(object.binding)
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
} }
