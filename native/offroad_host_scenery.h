// SPDX-License-Identifier: BSD-3-Clause
// Standalone host-owned Off Road ordinary scenery. No activation/CPU writes.
#pragma once
#include "offroad_model.h"
#include "offroad_transform.h"
#include "offroad_future_sections.h"
#include "offroad_distance.h"
#include "offroad_partial_sections.h"
#include <algorithm>
#include <map>
#include <set>

namespace cruisn { namespace offroad_host {
using scenery::Float;
using offroad_model::Quad;
struct Object
{
    uint32_t id=0,model=0,lod=0;
    int32_t depth=0,order=0;
    bool resident_margin=false;
    std::vector<Quad> quads;
    std::vector<std::array<uint32_t,4>> depths;
};
struct Scene
{
    uint32_t pending=0,future=0,unsupported=0,near=0,far=0,projection=0,material=0;
    uint32_t resident_margin=0;
    uint32_t resident_candidates=0;
    uint32_t resident_pruned=0;
    uint32_t partial_recovered=0;
    bool pretrack=false,partial=false,deferred=false;
    std::vector<Object> objects;
};
struct Cache
{
    uint32_t track=0;
    size_t words=0;
    std::map<uint32_t,offroad_model::Model> models;
    offroad_future::Cache future;
    void clear(){track=0;words=0;models.clear();future.clear();}
    template<class Read> const offroad_model::Model *get(Read read,uint32_t p)
    {
        auto it=models.find(p);if(it!=models.end())return &it->second;
        offroad_model::Model m;if(!offroad_model::load(read,p,m))return nullptr;
        const size_t n=3*m.vertices.size()+6*m.polygons.size();
        if(models.size()>=1024 || words+n>1048576){models.clear();words=0;}
        words+=n;return &models.emplace(p,std::move(m)).first->second;
    }
};
inline bool less(Float a,Float b){const auto d=a-b;return d.e!=-128 && d.m<0;}
inline std::array<Float,3> center(const std::array<uint32_t,22> &object,
    const std::array<uint32_t,12> &view)
{
    const std::array<Float,3> v={{Float::load(object[11]),Float::load(object[12]),Float::load(object[13])}};
    std::array<Float,3> out;
    for(unsigned i=0;i<3;++i)
    {const unsigned a=4*i;out[i]=((v[0]*Float::load(view[a])+Float::load(view[a+3]))+
        v[1]*Float::load(view[a+1]))+v[2]*Float::load(view[a+2]);}
    return out;
}
inline int32_t order(const std::array<Float,3> &position,Float scale)
{
    const auto x=position[0].reload()*scale,y=position[1].reload()*scale,z=position[2]*scale;
    return (((x*x+z*z)+y*y)*Float::integer(less(position[2],Float())?-1:1)).fix();
}
struct MaterialState
{
    uint32_t palette_end=0,texture_end=0;
    bool ready=false;
};
template<class Read> bool material_state(Read read,MaterialState &result)
{
    result=MaterialState{};
    const uint32_t count=read(0x11145),head=read(0x11143),tail=read(0x11144),busy=read(0x19e20);
    if(read(0x11141)!=0x9e0000 || read(0x11142)!=0x10390 || read(0x19e29)!=0xa00000 ||
        count>32 || head>=32 || tail>=32 || (head+count)%32!=tail || busy>1)return false;
    const uint32_t palettes=read(0x19e21),textures=read(0x19e23);
    if(palettes>128 || textures>16384)return false;
    result.palette_end=palettes*256;result.texture_end=textures*256;
    result.ready=!count && !busy;return true;
}
inline bool material_bound(const Quad &q,const MaterialState &state)
{
    if((q[0]&0x300)!=0x100)return uint32_t(q[1])+(q[0]&255)<state.palette_end;
    if(uint32_t(q[1])+255>=state.palette_end)return false;
    uint32_t u=0,v=0;
    for(unsigned i=10;i<14;++i){u=std::max(u,uint32_t(q[i]&255));v=std::max(v,uint32_t(q[i]>>8));}
    // One texel of interpolation allowance, conservatively bounded by the
    // complete allocated texture range. Live colors are never cached here.
    return uint64_t(q[14])*256+std::min(v+1,255U)*256+std::min(u+1,255U)<state.texture_end;
}

template<class Read> bool build(Read read,Scene &result,uint32_t multiplier,bool use_future,Cache &cache,
    bool clip_admission=false,bool retain_depths=false,bool recover_partial=false,
    bool resident_margins=false)
{
    result=Scene{};Scene scene;
    if(!offroad_distance::valid_multiplier(multiplier) || (clip_admission && (multiplier!=3 || !use_future)))return false;
    if(recover_partial && (multiplier!=3 || !use_future))return false;
    if(resident_margins && (multiplier!=3 || !use_future || retain_depths))return false;
    offroad_future::Frontier f;if(!offroad_future::frontier(read,f))return false;
    if(f.pretrack){cache.clear();scene.pretrack=true;result=scene;return true;}
    if(cache.track!=f.track){cache.clear();cache.track=f.track;}
    scene.partial=f.partial;
    MaterialState materials;if(!material_state(read,materials))return false;
    if(!materials.ready){scene.deferred=true;result=scene;return true;}
    const uint32_t view_ptr=read(0x1120b),pool=read(0x111ee);
    if(view_ptr>0x20000-12 || pool>0x20000-1200*22 || read(0x111f5)!=0x1b73e ||
        read(0x111a7)!=offroad_distance::table_base || read(0x1117b)!=0xc23e97)return false;
    std::array<uint32_t,12> view;for(unsigned i=0;i<12;++i)view[i]=read(view_ptr+i);
    const uint32_t addresses[]={0x19731,0x1b4bd,0x1d0af,0x1b4c1,0x1b4c2,0x1b4c3,0x1b4c4,
        0x1122a,0x1122b,0x1122c,0x1122d,0x1122e,0x1122f};
    std::array<uint32_t,13> context;for(unsigned i=0;i<13;++i)context[i]=read(addresses[i]);
    std::vector<std::pair<uint32_t,std::array<uint32_t,22>>> candidates;
    std::set<uint32_t> seen;uint32_t p=read(0x1b73e);
    while(p)
    {
        if(p<pool || (p-pool)%22 || p>=pool+1200*22 || !seen.insert(p).second)return false;
        std::array<uint32_t,22> o;for(unsigned i=0;i<22;++i)o[i]=read(p+i);
        candidates.emplace_back(p,o);p=o[0];++scene.pending;
    }
    if(use_future)
    {
        offroad_future::Result future;if(!offroad_future::collect(read,future,cache.future))return false;
        const size_t original_sources=future.sources.size();
        if(recover_partial && !offroad_future::recover_partial(read,future))return false;
        scene.partial_recovered=uint32_t(future.sources.size()-original_sources);
        for(const auto &source:future.sources)
        {
            if(!source.supported){++scene.unsupported;continue;}
            const uint32_t id=0x80000000|source.source;
            if(!seen.insert(id).second)return false;
            candidates.emplace_back(id,source.words);++scene.future;
        }
    }
    if(resident_margins)
    {
        // The loader has already materialized these ordinary descriptors. Only
        // allocated instances may contribute; a section header alone is not
        // evidence that its textures and object have become resident.
        const uint32_t free_head=read(0x111f6);
        if(free_head>=0x20000)return false;
        std::set<uint32_t> free;
        for(uint32_t p=read(free_head);p;p=read(p))
            if(p<pool || p>=pool+1200*22 || (p-pool)%22 || !free.insert(p).second)return false;
        std::map<uint32_t,uint32_t> allocated;
        for(uint32_t p=pool;p<pool+1200*22;p+=22)if(!free.count(p))
        {
            const auto key=read(p+6);
            if(!allocated.emplace(key,p).second)allocated[key]=0xffffffff;
        }
        offroad_future::Result loaded;if(!offroad_future::build(read,loaded,true))return false;
        for(const auto &source:loaded.sources)
        {
            if(!source.supported)continue;
            const auto owner=allocated.find(source.words[6]);
            if(owner==allocated.end() || owner->second==0xffffffff)continue;
            const uint32_t p=owner->second;
            if((read(p+5)&0x7fffffff)!=(source.words[5]&0x7fffffff))continue;
            bool match=true;
            for(unsigned i:{6U,7U,8U,11U,12U,13U,14U,15U,16U,17U,18U,19U,20U})
                if(read(p+i)!=source.words[i]){match=false;break;}
            if(!match)continue;
            const uint32_t id=0x40000000|source.source;
            if(!seen.insert(id).second)return false;
            candidates.emplace_back(id,source.words);
            ++scene.resident_candidates;
        }
    }
    for(const auto &entry:candidates)
    {
        const auto &o=entry.second;
        if(o[5]&0x200e){++scene.unsupported;continue;}
        if(!offroad_model::rom_span(o[20],7) || !offroad_model::rom_span(o[17],1))return false;
        const auto position=center(o,view);
        const auto radius=Float::load(read(o[20]));
        const auto nearest=position[2]-radius;
        if(less(nearest,Float::integer(1000))){++scene.near;continue;}
        // Candidate-only admission up to the existing projection limit. Every
        // vertex still passes the unchanged projection/material guards below.
        const auto admission=clip_admission?offroad_distance::original_clip:offroad_distance::original_far;
        if(!less(nearest,Float::integer(int32_t(admission*multiplier)))){++scene.far;continue;}
        std::array<uint32_t,12> matrix;
        if(!offroad_transform::prepare(o,view,[&](int32_t i){return read(uint32_t(0xc23e97+i));},matrix))return false;
        const auto lod=offroad_transform::select_lod(o,context).first;
        const auto *model=cache.get(read,o[20]+7+5*lod);if(!model)return false;
        std::vector<offroad_model::Vertex> projected;
        std::vector<uint32_t> camera_depths;
        if(!offroad_model::project(*model,matrix,read(0x11230),0x1e03,[&](int32_t i){
            return i<=63679?read(uint32_t(offroad_distance::table_base+i)):offroad_distance::reciprocal(i);
        },projected,multiplier,retain_depths?&camera_depths:nullptr)){++scene.projection;continue;}
        for(const auto &poly:model->polygons)if(!offroad_future::rom_span(o[17]+(poly[0]>>16),1))return false;
        Object out;out.id=entry.first;out.model=o[20];out.lod=lod;out.depth=position[2].reload().fix();
        out.order=order(position,Float::load(read(0x11238)));
        out.resident_margin=bool(out.id&0x40000000);
        if(!offroad_model::quads(*model,projected,(o[5]&read(0x11249))?0x2000:0,o[18],o[19],
            [&](uint32_t index){return read(o[17]+index);},out.quads,
            retain_depths?&camera_depths:nullptr,retain_depths?&out.depths:nullptr))return false;
        if(std::any_of(out.quads.begin(),out.quads.end(),[&](const Quad &q){return !material_bound(q,materials);}))
        {++scene.material;continue;}
        if(out.resident_margin)
        {
            out.quads.erase(std::remove_if(out.quads.begin(),out.quads.end(),[](const Quad &q){
                if(q[0]!=0x100)return true; // opaque ordinary textured ground only
                int16_t minx=int16_t(q[2]),maxx=minx;
                for(unsigned i:{4U,6U,8U}){minx=std::min(minx,int16_t(q[i]));maxx=std::max(maxx,int16_t(q[i]));}
                return minx>=0 && maxx<512;
            }),out.quads.end());
            if(out.quads.empty()){++scene.resident_pruned;continue;}
            scene.resident_margin+=uint32_t(out.quads.size());
        }
        scene.objects.push_back(std::move(out));
    }
    std::sort(scene.objects.begin(),scene.objects.end(),[](const Object &a,const Object &b){
        return a.order!=b.order?a.order>b.order:a.id<b.id;});
    result=std::move(scene);return true;
}
}} // namespace cruisn::offroad_host
