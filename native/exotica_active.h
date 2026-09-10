// SPDX-License-Identifier: BSD-3-Clause
// Current Exotica ordinary-list render operands. No historical ROM identity,
// allocations, writes, device submission or material-residency certification.
#pragma once
#include "exotica_transform.h"
#include <algorithm>
#include <cmath>
#include <set>

namespace cruisn { namespace exotica_active {
using scenery::Float;
struct Source
{
    // Deliberately a distinct type from exotica_future::Source. These identify
    // an ordinary list address and a CURRENT RAM object slot, respectively.
    uint32_t entry=0,source=0;
    bool supported=true;
    // Common rendering uses offsets0..30. Offset31 is zero padding for the
    // shared geometry DTO, never read from a neighboring object's allocation.
    std::array<uint32_t,32> words{};
};
constexpr size_t max_objects=4096;
inline bool valid(const Source &s)
{return s.entry>=0xbbb5 && s.entry<=0xbbb8 && s.source>=0x1000 && uint64_t(s.source)+31<=0x40000 && !s.words[31];}

template<class Read> bool read_list(uint32_t entry,uint32_t head,Read read,std::vector<Source> &result)
{
    result.clear();
    if(entry<0xbbb5 || entry>0xbbb8 || head<0x1000 || head>=0x40000)return false;
    std::set<uint32_t> seen{head};std::vector<Source> out;
    for(uint32_t pointer=read(head);pointer;)
    {
        Source s;s.entry=entry;s.source=pointer;
        if(!valid(s) || out.size()>=max_objects || !seen.insert(pointer).second)return false;
        for(unsigned i=0;i<31;++i)s.words[i]=read(pointer+i);
        pointer=s.words[0];out.push_back(s);
    }
    result=std::move(out);return true;
}
struct Parameters
{
    uint32_t mode=0,projection_table=0,margin=0;
    std::array<uint32_t,3> camera{};
    std::array<uint32_t,9> view{},alternate{};
    std::array<uint32_t,14> constants{}; //67ce..67db, captured for this list
};
enum class Reason : uint32_t { unsupported=0,distance=1,vertical_low=2,vertical_high=3,left=4,right=5,admitted=6 };
struct Decision
{
    Reason stock=Reason::unsupported,wide=Reason::unsupported;
    uint32_t flags=0,index=0,factor=0;
    int32_t depth=0;
    std::array<uint32_t,3> translation{};
    bool margin_candidate=false;
};
inline double value(const Float &f)
{return f.e==-128?0.:std::ldexp(double(int64_t(f.m)^INT64_C(0x80000000)),f.e-31);}

// Reproduce the original asymmetric sphere planes, changing only horizontal
// extent for the wide decision. Current fade, vertical and far limits stay put.
// Near-plane-crossing objects can be admitted here with depth<=0; the geometry
// adapter still excludes them explicitly. Do not equate admission with drawing.
template<class Read> bool classify(const Source &s,const Parameters &p,Read read,Decision &result)
{
    result=Decision();
    if(!valid(s) || p.margin>256 || uint64_t(p.projection_table)+5000>0x40000 ||
        p.constants[0]!=Float::integer(511).store() || p.constants[2]!=Float::integer(256).store() ||
        p.constants[3]!=Float::integer(200).store() || p.constants[12]!=204800)return false;
    Decision out;out.flags=s.words[15]&~uint32_t((p.mode&0x100)?0:0x400);
    if(!s.supported || out.flags&0x80 || ((out.flags&3)!=0 && (out.flags&3)!=3))
    {result=out;return true;}
    const int32_t radius=int32_t(s.words[21]);
    if(radius<0 || radius>=10000000)return false;
    std::array<uint32_t,3> position;std::array<uint32_t,9> rotation;
    std::copy_n(s.words.begin()+1,3,position.begin());std::copy_n(s.words.begin()+5,9,rotation.begin());
    exotica_transform::Prepared t;
    if(!exotica_transform::prepare(position,p.camera,p.view,rotation,p.alternate,out.flags,t))return false;
    out.depth=t.depth;out.translation=t.translation;
    const int64_t distance=int64_t(t.depth)+radius;
    if(distance<INT32_MIN || distance>INT32_MAX)return false; //reject guest integer overflow
    if(distance<0 || distance>int64_t(p.constants[12]))
    {out.stock=out.wide=Reason::distance;result=out;return true;}
    out.index=std::min(uint32_t(std::max(t.depth,0))/16,4999U);
    out.factor=read(p.projection_table+out.index);
    const auto f=Float::load(out.factor),r=Float::integer(radius)*f;
    if(value(f)<=0)return false;
    const auto x=Float::load(t.translation[0])*f,y=Float::load(t.translation[1])*f;
    if(value((y+r)+Float::load(p.constants[3]))<0)out.stock=out.wide=Reason::vertical_low;
    else if(value(y-r)>value(Float::load(p.constants[3])))out.stock=out.wide=Reason::vertical_high;
    else
    {
        auto horizontal=[&](uint32_t margin){
            const auto lower=(x+r)+(Float::load(p.constants[2])+Float::integer(int32_t(margin)));
            if(value(lower)<0)return Reason::left;
            if(value((lower-r)-r)>value(Float::load(p.constants[0])+Float::integer(int32_t(2*margin))))return Reason::right;
            return Reason::admitted;
        };
        out.stock=horizontal(0);out.wide=horizontal(p.margin);
    }
    out.margin_candidate=(out.stock==Reason::left || out.stock==Reason::right) && out.wide==Reason::admitted;
    result=out;return true;
}
} }
