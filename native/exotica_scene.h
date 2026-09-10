// SPDX-License-Identifier: BSD-3-Clause
// Bounded private Exotica scene assembly. No guest writes, FIFO or GPU calls.
// This describes geometry/material requests; it does NOT certify live residency,
// source eligibility, scene insertion, or handover to original game objects.
#pragma once
#include "exotica_future_sections.h"
#include "exotica_active.h"
#include "exotica_transform.h"
#include "exotica_state.h"
#include "zeus_state.h"
#include "zeus_model.h"
#include "zeus_model_bounds.h"
#include <map>
#include <set>

namespace cruisn { namespace exotica_scene {
struct Parameters
{
    uint32_t frame=0,far_limit=204800,multiplier=1,scale=0,render_policy=0;
    float margin=0;
    bool complete_fade=false,frustum_bounds=false;
    // Optimization strategy only; context serialization still describes the
    // same geometry inputs. Runtime mode is separately frozen in recording env.
    uint32_t early_depth=0; //0 full transform,1 early reject,2 compare all depths
    std::array<uint32_t,3> camera{};
    std::array<uint32_t,9> view{},alternate{};
    exotica_state::Operands setup;
    zeus_state::Context context;
};
struct Instance
{
    uint32_t entry=0,source=0,descriptor=0,base=0,count=0,band=0;
    uint32_t palette=0,palette_control=0;
    int32_t depth=0;
    size_t first_quad=0,quad_count=0;
};
struct Result
{
    std::vector<Instance> instances;
    std::vector<zeus_model::Quad> quads;
    size_t selected=0,unsupported_transform=0,culled_distance=0,culled_bounds=0;
    size_t model_words_read=0,decoded_polygons=0,viewport_polygons=0;
    size_t depth_tests=0,depth_verified=0,depth_skipped=0;
    float maximum_depth=0;
};
constexpr size_t max_sources=32768,max_instances=4096,max_quads=131072,max_model_words=4*1024*1024;

// Every polygon must have an explicit format and texture base in its own model.
// Private geometry must not borrow these from an unrelated original submission.
inline bool explicit_texture(const std::vector<uint32_t> &words,uint32_t quad_size)
{
    bool format=false,texture=false;
    for(size_t i=0;i<words.size();)
    {
        const auto *d=&words[i];const unsigned op=d[0]>>24,n=op==0x38?quad_size:2;
        if(!n || n>words.size()-i)return false;
        i+=n;
        if(op==0 || op==0x22)
        {
            const int shift=int((d[0]>>16)&255)-0x9d;
            if(shift<-31 || shift>31)return false;
            format=true;
        }
        else if(op==0x36 && ((d[0]>>16)&127)==0x20 && d[1]>>24==5)texture=true;
        else if(op==0x38 && (!format || !texture))return false;
    }
    return true;
}

inline bool intersects(const zeus_model::Quad &q,float margin)
{
    float left=q.vertices[0][0],right=left,top=q.vertices[0][1],bottom=top;
    for(unsigned i=1;i<q.state[1];++i)
    {
        left=std::min(left,q.vertices[i][0]);right=std::max(right,q.vertices[i][0]);
        top=std::min(top,q.vertices[i][1]);bottom=std::max(bottom,q.vertices[i][1]);
    }
    return right>=-margin && left<=512+margin && bottom>=0 && top<=400;
}

// Read supplies checked C32 words. ModelRead must copy exactly the requested
// current WaveRAM words into owned storage, with bounds checked by the caller.
// Select owns source eligibility; choosing every historical descriptor is not
// safe for dynamic objects. Every call starts with a fresh, bounded model cache.
namespace detail {
template<class Source,class Read,class ModelRead,class Select,class Identity>
bool build_sources(const std::vector<Source> &sources,const Parameters &p,
    Read read,ModelRead model_read,Select select,Identity valid_identity,Result &result)
{
    result=Result();
    if(sources.size()>max_sources || p.far_limit!=204800 || p.multiplier<1 || p.multiplier>3 ||
        !std::isfinite(p.margin) || p.margin<0 || p.margin>256 || p.render_policy || p.early_depth>2 || !zeus_state::valid(p.context))return false;
    if(read(0x67da)!=p.far_limit || read(0x67db)!=p.scale)return false;
    Result out;
    struct CachedModel
    {
        std::vector<uint32_t> words;
        std::map<uint32_t,zeus_bounds::Bounds> bounds;
    };
    std::map<std::pair<uint32_t,uint32_t>,CachedModel> cache;
    std::set<std::pair<uint32_t,uint32_t>> identities;
    for(const auto &s:sources)
    {
        if(!s.supported || !select(s))continue;
        if(!valid_identity(s) || !identities.emplace(s.entry,s.source).second)return false;
        ++out.selected;const auto &o=s.words;uint32_t flags=o[15];
        if(((flags&3)!=0 && (flags&3)!=3) || flags&0x80)
        {++out.unsupported_transform;continue;}
        std::array<uint32_t,3> position;std::array<uint32_t,9> rotation;
        std::copy_n(o.begin()+1,3,position.begin());std::copy_n(o.begin()+5,9,rotation.begin());
        exotica_transform::Prepared transform;
        int32_t depth=0;
        if(p.early_depth)
        {
            if(!exotica_transform::camera_depth(position,p.camera,p.view,flags,depth))return false;
            ++out.depth_tests;
        }
        if(p.early_depth!=1)
        {
            if(!exotica_transform::prepare(position,p.camera,p.view,rotation,p.alternate,flags,transform))return false;
            if(p.early_depth==2)
            {if(depth!=transform.depth)return false;++out.depth_verified;}
            else depth=transform.depth;
        }
        const int32_t radius=int32_t(o[21]);const int64_t distance=int64_t(depth)+radius;
        if(radius<0 || radius>=10000000)return false;
        if(depth<=0 || distance>int64_t(p.far_limit)*p.multiplier)
        {++out.culled_distance;if(p.early_depth==1)++out.depth_skipped;continue;}
        if(p.early_depth==1 &&
            (!exotica_transform::prepare(position,p.camera,p.view,rotation,p.alternate,flags,transform) ||
             depth!=transform.depth))return false;
        if(out.instances.size()>=max_instances || !exotica_future::span(o[17],6))return false;
        const uint32_t descriptor=exotica_transform::select_model(o[17],read(o[17]),transform.depth);
        if(!exotica_future::span(descriptor,6))return false;
        const uint32_t base=read(descriptor+3),count=read(descriptor+4);
        const uint64_t block=(base%1024)+((base>>16)%2048)*1024;
        const size_t size=2*(size_t(count)+1);
        if(!base || count>0xc800 || block*2+size>4*1024*1024)return false;
        const auto key=std::make_pair(base,count);
        auto found=cache.find(key);
        if(found==cache.end())
        {
            if(size>max_model_words-out.model_words_read)return false;
            std::vector<uint32_t> words;
            if(!model_read(base,count,words) || words.size()!=size)return false;
            out.model_words_read+=size;CachedModel model;model.words=std::move(words);
            found=cache.emplace(key,std::move(model)).first;
        }
        auto operands=p.setup;operands.object=o;operands.cache.fill(UINT32_MAX);
        if(p.complete_fade)flags&=~uint32_t(0x04000100);
        operands.flags=flags;exotica_state::Result setup;
        if(!exotica_state::setup(operands,setup))return false;
        auto packet=std::move(setup.packet);
        const auto placement=exotica_transform::packet(transform,p.scale,true);
        packet.insert(packet.end(),placement.begin(),placement.end());
        zeus_state::Result state;
        if(!zeus_state::transition(p.context,{},packet,base,state))return false;
        if(state.context.regs[0x40]!=0x0084003f ||
            !explicit_texture(found->second.words,state.context.quad_size))return false;
        zeus_model::Context context;
        context.frame=p.frame;context.quad_size=state.context.quad_size;
        context.texture=state.context.texture;context.yscale=state.context.yscale;
        context.regs=state.context.regs;context.render=state.context.render;
        context.matrix=state.context.matrix;
        std::copy_n(state.context.translation.begin(),3,context.translation.begin());
        // This initial assembler covers legacy policy only. A policy extension
        // must be explicit and independently compared before use.
        context.render_policy=0;
        if(p.frustum_bounds)
        {
            auto &model=found->second;auto bound=model.bounds.find(context.quad_size);
            if(bound==model.bounds.end())
            {
                zeus_bounds::Bounds prepared;
                if(!zeus_bounds::prepare(model.words,context.quad_size,prepared))return false;
                bound=model.bounds.emplace(context.quad_size,prepared).first;
            }
            // Retain full projection when depth could violate the assembler's
            // existing numeric guard, even if the model is entirely offscreen.
            if(zeus_bounds::outside(bound->second,context,p.margin,2147483520.f))
            {++out.culled_bounds;continue;}
        }
        zeus_model::Result decoded;
        if(!zeus_model::decode(found->second.words,context,decoded) || decoded.quads.size()>max_quads-out.quads.size())return false;
        Instance instance;instance.entry=s.entry;instance.source=s.source;instance.descriptor=descriptor;
        instance.base=base;instance.count=count;instance.depth=transform.depth;
        instance.band=uint32_t((distance-1)/p.far_limit)+1;
        instance.palette=state.context.palette;instance.palette_control=state.context.regs[0x40];
        instance.first_quad=out.quads.size();instance.quad_count=decoded.quads.size();
        for(const auto &q:decoded.quads)
        {
            if(intersects(q,p.margin))++out.viewport_polygons;
            const int32_t bias=int32_t(q.state[10]);
            for(unsigned i=0;i<q.state[1];++i)
            {
                const float depth=q.vertices[i][2]+float(std::max(bias,0));
                if(!std::isfinite(depth) || depth>=2147483520.f)return false;
                out.maximum_depth=std::max(out.maximum_depth,depth);
            }
        }
        out.decoded_polygons+=decoded.polygons;
        out.quads.insert(out.quads.end(),decoded.quads.begin(),decoded.quads.end());
        out.instances.push_back(instance);
    }
    result=std::move(out);return true;
}
} //detail

template<class Read,class ModelRead,class Select>
bool build(const std::vector<exotica_future::Source> &sources,const Parameters &p,
    Read read,ModelRead model_read,Select select,Result &result)
{
    return detail::build_sources(sources,p,read,model_read,select,[](const exotica_future::Source &s){
        return exotica_future::span(s.entry,4) && exotica_future::span(s.source,6);
    },result);
}

// Caller provides current, independently selected list members. Active identity
// is never accepted by the future-ROM overload. Duplicated slots across lists
// reject the whole scene; selection must not hide contradictory ownership.
template<class Read,class ModelRead>
bool build_active(const std::vector<exotica_active::Source> &sources,const Parameters &p,
    Read read,ModelRead model_read,Result &result)
{
    result=Result();
    if(p.multiplier!=1 || p.complete_fade || sources.size()>exotica_active::max_objects)return false;
    std::set<uint32_t> objects;
    for(const auto &s:sources)if(!exotica_active::valid(s) || !objects.insert(s.source).second)return false;
    return detail::build_sources(sources,p,read,model_read,[](const exotica_active::Source &){return true;},
        [](const exotica_active::Source &s){return exotica_active::valid(s);},result);
}
} }
