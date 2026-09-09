// SPDX-License-Identifier: BSD-3-Clause
// Off Road 1.63 ordinary section descriptors. Standalone: no guest writes/draws.
#pragma once
#include <array>
#include <cstdint>
#include <vector>

namespace cruisn { namespace offroad_future {
constexpr uint32_t excluded_flags=0x3f800000;
struct Frontier
{
    uint32_t track=0,count=0,current=0,front=0,back=0;
    bool pretrack=false,partial=false;
};
struct Source
{
    uint32_t entry=0,source=0,number=0,ordinal=0,flags=0;
    bool supported=false;
    std::array<uint32_t,22> words{};
};
struct Result
{
    Frontier frontier;
    std::vector<Source> sources;
};
inline bool rom_span(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=65536 && uint64_t(p)+n<=0x1000000;}

template<class Read> bool code_matches(Read read)
{
    const uint32_t code[][2]={{0x9b63,0x082cb4b7},{0x9b7b,0x62009c24},
        {0x9b80,0x152cb4b7},{0x9bbd,0x62009c24},{0x9c27,0x085b1210},
        {0x9c32,0x62009c68},{0x9c34,0x032011c2},{0x9c5e,0x08400205},
        {0x9c68,0x6200184d},{0x9c69,0x0820b4cd},{0x1bf8,0x082a11f4},
        {0x111c2,0x23000000},{0x111c3,0x23000000},{0x111c4,0x03000000},
        {0x1123e,0x10000000},{0x11245,0x00800000},{0x11240,0x08000000}};
    for(const auto &pair:code)if(read(pair[0])!=pair[1])return false;
    return true;
}

// The current section can advance one scene before the front entry/lead settle.
// Exclude that entire uncertain section. Larger mismatches remain unsupported.
template<class Read> bool frontier(Read read,Frontier &result)
{
    result=Frontier{};Frontier f;
    f.track=read(0x1b4b4);f.count=read(0x1b4cc);
    const uint32_t current=read(0x1b4b5),front=read(0x1b4b7),back=read(0x1b4ba);
    if(!f.track && !f.count && !current && !front && !back)
    {f.pretrack=true;result=f;return true;}
    if(!f.count || f.count>128 || !rom_span(f.track,4*f.count) || read(0x1b4bd)!=1)return false;
    for(uint32_t i=0;i<f.count;++i)
    {
        const uint32_t p=f.track+4*i,flags=read(p);
        if(read(p+1)!=i || bool(flags&1)!=(i==0) || bool(flags&0x80000000)!=(i+1==f.count))return false;
    }
    auto index=[&](uint32_t p,uint32_t &i){
        if(p<f.track || (p-f.track)%4 || (p-f.track)/4>=f.count)return false;
        i=(p-f.track)/4;return true;};
    if(!index(current,f.current) || !index(front,f.front) || !index(back,f.back) ||
        f.back>f.current || f.current>f.front || read(0x1b4b6)!=f.current ||
        read(0x1b4b8)!=f.front || read(0x1b4bb)!=f.back ||
        read(0x1b4bc)!=f.current-f.back)return false;
    const uint32_t lead=read(0x1b4b9),loaded_lead=f.front-f.current;
    if(lead==loaded_lead+1 && f.front+1<f.count)f.partial=true;
    else if(lead!=loaded_lead)return false;
    result=f;return true;
}

// Material addresses are rebound on each call. They are not residency proof;
// palette colors, upload readiness and texture lifetime need separate checks.
inline bool descriptor(const std::array<uint32_t,11> &input,uint32_t number,
    uint32_t ordinal,uint32_t count,const std::array<uint32_t,3> &binding,Source &out)
{
    out.words={};out.flags=input[0];out.number=number;out.ordinal=ordinal;
    out.supported=false;
    if(!count || count>256 || ordinal>=count || number>255)return false;
    if(input[0]&excluded_flags)return true; // Loader/custom/alternate binding classes.
    if(!rom_span(input[1],7) || !rom_span(binding[0],1) || binding[1]>0x7fff || binding[2]>0xffff)return false;
    auto &o=out.words;o[5]=input[0];
    o[6]=((count-1-ordinal)<<24)|(number<<16)|0x8000;
    o[7]=input[3];o[8]=input[2];
    for(unsigned i=0;i<6;++i)o[11+i]=input[5+i];
    o[17]=binding[0];o[18]=binding[1];o[19]=binding[2];o[20]=input[1];
    out.supported=true;return true;
}

template<class Read> bool build(Read read,Result &result,bool loaded=false)
{
    result=Result{};Result out;
    if(!frontier(read,out.frontier))return false;
    const auto &f=out.frontier;
    if(f.pretrack){result=out;return true;}
    const std::array<uint32_t,3> binding={{read(0x1b4cd),read(0x1b4cf),read(0x1b4ce)}};
    const uint32_t first=loaded?f.back:f.front+1+uint32_t(f.partial),last=loaded?f.front+1:f.count;
    for(uint32_t number=first;number<last;++number)
    {
        const uint32_t entry=f.track+4*number,data=read(entry+3);
        if(!rom_span(data,17))return false;
        const uint32_t count=read(data+16);
        if(!count || count>256 || !rom_span(data+17,11*count) || out.sources.size()+count>32768)return false;
        for(uint32_t ordinal=0;ordinal<count;++ordinal)
        {
            Source source;source.entry=entry;source.source=data+17+11*ordinal;
            std::array<uint32_t,11> words;
            for(unsigned i=0;i<11;++i)words[i]=read(source.source+i);
            if(!descriptor(words,number,ordinal,count,binding,source))return false;
            out.sources.push_back(source);
        }
    }
    result=std::move(out);return true;
}

struct Cache
{
    bool valid=false;
    Result value;
    void clear(){valid=false;value=Result{};}
};
// Cache immutable section operands between frontier changes. Live binding
// addresses are refreshed even when the track/frontier key is unchanged.
template<class Read> bool collect(Read read,Result &result,Cache &cache)
{
    result=Result{};Frontier f;
    if(!frontier(read,f))return false;
    if(f.pretrack){cache.clear();result.frontier=f;return true;}
    const auto &old=cache.value.frontier;
    if(!cache.valid || old.track!=f.track || old.count!=f.count || old.front!=f.front || old.partial!=f.partial)
    {
        Result value;if(!build(read,value))return false;
        cache.value=std::move(value);cache.valid=true;
    }
    const uint32_t lookup=read(0x1b4cd),palette=read(0x1b4cf),texture=read(0x1b4ce);
    if(!rom_span(lookup,1) || palette>0x7fff || texture>0xffff)return false;
    result=cache.value;result.frontier=f;
    for(auto &source:result.sources)if(source.supported)
    {source.words[17]=lookup;source.words[18]=palette;source.words[19]=texture;}
    return true;
}
}} // namespace cruisn::offroad_future
