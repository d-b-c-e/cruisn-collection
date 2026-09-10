// SPDX-License-Identifier: BSD-3-Clause
// Exotica 2.4 render descriptors before activation; no guest writes or drawing.
#pragma once
#include "world_future_sections.h" // Shared independently checked C31 yaw polynomial.

namespace cruisn { namespace exotica_future {
using scenery::Float;
struct Section
{
    uint32_t entry=0,index=0,cursor=0,heading=0x80000000,section_heading=0x80000000,gap=0,flags=0;
    std::array<uint32_t,3> position{};
    std::array<uint32_t,9> matrix{};
    std::array<uint32_t,5> header{};
    bool initial=false;
};
struct Source
{
    uint32_t entry=0,source=0,index=0,ordinal=0;
    bool supported=false,future=false;
    std::array<uint32_t,32> words{};
};
struct Result
{
    bool pretrack=false,partial=false;
    uint32_t frontier=0;
    std::vector<Section> sections;
    std::vector<Source> sources;
};
inline bool span(uint32_t p,uint32_t n)
{return p>=0xa00000 && n>0 && n<=65536 && uint64_t(p)+n<=0x1000000;}

template<class Read> bool code_matches(Read read)
{
    const uint32_t code[][2]={{0xb7e8,0x082e0597},{0xb804,0x08442501},{0xb817,0x152e0597},
        {0xb842,0x084a2501},{0xb859,0x082267c4},{0xb86f,0x14420416},{0xb878,0x08402501},
        {0xb8cb,0x0840041d},{0xbc36,0x08400202},{0xa032,0x0221e67c},{0xa025,0x0221e67d},
        {0x92e8,0x24e02122},{0x92f8,0xc00201c1},{0xb840,0x1420059b},{0xbbaa,0x80000},{0xbbb1,0x4000000}};
    for(const auto &r:code)if(read(r[0])!=r[1])return false;
    return true;
}
inline std::array<Float,3> transform(const std::array<Float,3> &v,const std::array<uint32_t,9> &matrix)
{
    std::array<Float,9> m;for(unsigned i=0;i<9;++i)m[i]=Float::load(matrix[i]);
    return {{((v[0]*m[0]+v[1]*m[1])+v[2]*m[2]).reload(),
        ((v[0]*m[3]+v[1]*m[4])+v[2]*m[5]).reload(),
        (v[1]*m[7]+(v[2]*m[8]+v[0]*m[6])).reload()}};
}
template<class Read> bool binding(Read read,uint32_t token,uint32_t table,uint32_t &value)
{
    if(table>0x3fff0)return false;
    const uint32_t base=read(table+(token>>28)),index=token&0x3fff;
    if(!span(base,index+1))return false;
    value=read(base+index);return true;
}
inline bool descriptor(const std::array<uint32_t,6> &d,const std::array<uint32_t,6> &model,
    const Section &section,const std::array<uint32_t,11> &constants,const std::array<uint32_t,7> &trig,
    const std::array<uint32_t,2> &materials,Source &out)
{
    out.supported=false;out.words={};const uint32_t type=d[5]&0xf00;
    if(d[0]>>24 || type==0xa00 || type==0xf00)return true;
    if(!span(d[0],6))return false;
    std::array<Float,3> v;
    for(unsigned i=0;i<3;++i)
    {
        v[i]=Float::integer(int32_t(d[i+1]));
        if(section.flags&1)v[i]=v[i]-Float::load(section.header[i]);
        v[i]=v[i].reload();
    }
    const auto position=transform(v,section.matrix);
    auto heading=Float::load(d[4])+Float::load(section.heading);
    if(section.flags&1)heading=heading-Float::load(section.header[3])+Float::load(0x01491000);
    const auto rotation=(heading-Float::load(section.section_heading)).e==-128?
        section.matrix:world_future::yaw(heading,trig);
    auto &o=out.words;
    for(unsigned i=0;i<3;++i)o[1+i]=(position[i]+Float::load(section.position[i])).store();
    for(unsigned i=0;i<9;++i)o[5+i]=rotation[i];
    o[14]=d[5]&0xfff;o[15]=model[5]|((d[5]&0xf000)<<4)|0x30;
    o[16]=2;o[17]=d[0];o[18]=materials[0];o[19]=materials[1];o[21]=model[1];
    o[22]=(((d[5]&0xf000)<<4)&constants[0])?0x077e0000:heading.store();
    uint32_t offset=(d[5]>>26)&63;if(section.flags&1)offset=section.gap-offset;
    o[29]=offset+section.cursor;
    if(!section.initial && !(o[15]&0x4900)){o[15]|=0x100|constants[7];o[16]|=0x78080000;}
    if(type==0xb00 || type==0xc00)
    {
        const unsigned map[][2]={{8,1},{16,2},{32,8},{64,9},{128,10}};
        for(const auto &item:map)if(section.flags&item[0])o[15]|=constants[item[1]];
        const uint32_t tag=d[5]&255;o[24]=((section.flags&1)?255-tag:tag)|(section.index<<8);
    }
    out.supported=true;return true;
}

// partial must cover the entire loader transaction, through its final position
// write at B840. It is not inferred from the current CPU PC after a coroutine yields.
// A mismatch in frontier scalars rejects the entire result without guest changes.
template<class Read> bool build(Read read,Result &result,bool partial=false)
{
    result=Result{};Result out;
    if(!code_matches(read))return false;
    const uint32_t entry=read(0x597),number=read(0x590),cursor=read(0x598);
    if(!entry && !number && !cursor){out.pretrack=true;result=out;return true;}
    const uint64_t table=uint64_t(read(0xe9))+read(0x1fbc);
    if(table>UINT32_MAX || !span(uint32_t(table),1))return false;
    const uint32_t track=read(uint32_t(table));
    if(!span(track,3) || entry<track+3 || (entry-track-3)%4)return false;
    std::array<uint32_t,7> trig;for(unsigned i=0;i<7;++i)trig[i]=read(0xe991+i);
    std::array<uint32_t,11> constants;for(unsigned i=0;i<11;++i)constants[i]=read(0xbbaa+i);
    std::array<uint32_t,3> position={{0x80000000,0x80000000,0x80000000}};
    uint32_t heading=0x80000000,offset=0;bool matched=false,ended=false;
    auto frontier_matches=[&](uint32_t index){
        if(offset!=cursor || number!=index*256 || heading!=read(0x59c))return false;
        for(unsigned i=0;i<3;++i)if(position[i]!=read(0x599+i))return false;
        return true;};
    for(uint32_t index=0;index<128;++index)
    {
        const uint32_t pointer=track+3+4*index;if(!span(pointer,4))return false;
        std::array<uint32_t,4> lists;for(unsigned i=0;i<4;++i)lists[i]=read(pointer+i);
        if(std::all_of(lists.begin(),lists.end(),[](uint32_t x){return x==UINT32_MAX;}))
        {ended=true;if(pointer==entry && !partial)matched=frontier_matches(index);break;}
        if(lists[0]<4 || !span(lists[0]-4,5))return false;
        Section section;section.entry=pointer;section.index=index;section.cursor=offset;
        section.position=position;section.heading=heading;section.flags=lists[3];section.initial=index<2;
        for(unsigned i=0;i<5;++i)section.header[i]=read(lists[0]-4+i);
        section.gap=(section.header[4]>>16)&255;
        auto angle=Float::load(heading);
        if(section.flags&1)angle=angle-Float::load(section.header[3])+Float::load(0x01491000);
        section.section_heading=angle.store();section.matrix=world_future::yaw(angle,trig);
        out.sections.push_back(section);
        if(pointer==entry)matched=frontier_matches(index);
        for(unsigned list_index=0;list_index<3;++list_index)
        {
            const uint32_t base=lists[list_index];if(!base)continue;
            if(!span(base,1))return false;
            const uint64_t count=uint64_t(list_index?read(base):read(base)&65535)+1;
            if(count>4096 || !span(base+1,uint32_t(6*count)) || out.sources.size()+count>32768)return false;
            for(uint32_t ordinal=0;ordinal<count;++ordinal)
            {
                Source source;source.entry=pointer;source.source=base+1+6*ordinal;
                source.index=index;source.ordinal=ordinal;source.future=uint64_t(pointer)>=uint64_t(entry)+4*partial;
                std::array<uint32_t,6> d;for(unsigned i=0;i<6;++i)d[i]=read(source.source+i);
                if(!(d[0]>>24) && (d[5]&0xf00)!=0xa00 && (d[5]&0xf00)!=0xf00)
                {
                    if(!span(d[0],6))return false;
                    std::array<uint32_t,6> model;for(unsigned i=0;i<6;++i)model[i]=read(d[0]+i);
                    const uint32_t material=model[2],override_index=(d[5]>>16)&1023;
                    std::array<uint32_t,2> bindings;
                    if(!binding(read,material&0xf0003fff,read(0xe67c),bindings[1]))return false;
                    const uint32_t bank=read(0xf5);if(bank>15)return false;
                    const uint32_t token=override_index?(override_index|(bank<<28)):
                        (material&0xf0000000)|((material&0x0fffc000)>>14);
                    if(!binding(read,token,read(0xe67d),bindings[0]))return false;
                    Section context=section;if(list_index==2)context.flags&=~1U;
                    if(!descriptor(d,model,context,constants,trig,bindings,source))return false;
                }
                out.sources.push_back(source);
            }
        }
        std::array<Float,3> delta;
        for(unsigned i=0;i<3;++i){delta[i]=Float::load(section.header[i]);if(section.flags&1)delta[i]=-delta[i];}
        const auto advance=transform(delta,section.matrix);
        for(unsigned i=0;i<3;++i)position[i]=(advance[i]+Float::load(position[i])).store();
        heading=((section.flags&1)?Float::load(heading)-Float::load(section.header[3]):
            Float::load(section.header[3])+Float::load(heading)).store();
        offset+=section.gap+1;
    }
    if(!ended || !matched)return false;
    out.frontier=entry;out.partial=partial;result=std::move(out);return true;
}
} }
