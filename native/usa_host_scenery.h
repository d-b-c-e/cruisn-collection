// SPDX-License-Identifier: BSD-3-Clause
// USA 4.5 pending scenery. Caller supplies direct RAM and checked ROM reads.
#pragma once
#include "usa_model.h"
#include <map>
#include <set>

namespace cruisn { namespace usa_host {
using usa_model::Float;
using usa_model::Quad;
struct Object
{
    uint32_t id=0,model=0;
    int32_t depth=0;
    std::vector<Quad> quads;
};
struct Scene
{
    uint32_t pending=0,unsupported=0,near=0,far=0,projection=0,decoded=0;
    uint32_t future=0;
    std::vector<Object> objects;
};
struct Descriptor
{
    uint32_t id=0;
    std::array<uint32_t,32> words{};
};
// USA model operands reside in immutable ROM. Palette bindings and projected
// vertices are deliberately excluded from this bounded host-only cache.
struct ModelCache
{
    std::map<uint32_t,usa_model::Model> models;
    size_t words=0;
    void clear(){models.clear();words=0;}
    template<class Read> const usa_model::Model *get(Read read,uint32_t address)
    {
        auto found=models.find(address);
        if(found!=models.end())return &found->second;
        usa_model::Model model;if(!usa_model::load(read,address,model))return nullptr;
        const size_t size=2+2*model.vertices.size()+5*model.polygons.size();
        if(models.size()>=1024 || words+size>1048576)clear();
        words+=size;
        return &models.emplace(address,std::move(model)).first->second;
    }
};
inline bool ram_span(uint32_t p,uint32_t n)
{return n<=8192 && uint64_t(p)+n<=0x20000;}
inline bool fast_span(uint32_t p,uint32_t n)
{return p>=0x809800 && n<=2048 && uint64_t(p)+n<=0x80a000;}
inline bool code_matches(const uint32_t *ram,size_t words)
{
    if(!usa_distance::code_matches(ram,words,80000) || !usa_distance::residency_matches(ram,words))return false;
    for(const auto &op:{world_distance::word{0x7d,0x08280043},{0x7e,0x62000166},
        {0x80,0x08280040},{0x81,0x62000166},{0x83,0x08280042},{0x84,0x62000166},
        {0x86,0x08280044},{0x87,0x62000166},{0x166,0x0840c000},
        {0x129,0x085b2101},{0x12c,0x082b004f},{0x140,0x64000162},{0x15d,0x24c00182},
        {0x49a,0x0831004f},{0x188,0x085b2101},{0x18b,0x082b004f},{0x1bb,0x6a00ffa7},
        {0x163,0x0e330000},{0x28d,0x0846000e},{0x29a,0x08330062},{0x477,0x08422102},{0x48f,0x08200083}})
        if(ram[op.address]!=op.value)return false;
    return true;
}
template<class Read> bool build(Read read,Scene &result,uint32_t far=80000,
    const std::vector<Descriptor> *future=nullptr,ModelCache *cache=nullptr)
{
    result=Scene{};
    if(far!=80000 && far!=160000 && far!=240000)return false;
    if(read(0x41)!=0xc9b4 || read(0x52)!=usa_distance::reciprocal_base)return false;
    const uint32_t cam=read(0x45),view=read(0x47),bill=read(0x4d),compact_bill=read(0x4e);
    const uint32_t palette_table=read(0x62),mode=read(0xc8f5),enabled=read(0xe8a1);
    if(!fast_span(cam,3) || !fast_span(view,9) || !fast_span(bill,9) || !fast_span(compact_bill,4) ||
       !ram_span(palette_table,1))return false;
    std::array<uint32_t,3> camera;
    std::array<uint32_t,9> matrix,billboard;
    std::array<uint32_t,4> compact_billboard;
    for(unsigned i=0;i<3;++i)camera[i]=read(cam+i);
    for(unsigned i=0;i<9;++i){matrix[i]=read(view+i);billboard[i]=read(bill+i);}
    for(unsigned i=0;i<4;++i)compact_billboard[i]=read(compact_bill+i);
    Scene scene;std::set<uint32_t> seen;std::vector<Descriptor> candidates;
    uint32_t id=read(0xc9b4);
    while(id)
    {
        if(id<0x1000 || !ram_span(id,32) || seen.size()>=2048 || !seen.insert(id).second)return false;
        Descriptor descriptor;descriptor.id=id;
        for(unsigned i=0;i<32;++i)descriptor.words[i]=read(id+i);
        id=descriptor.words[0];++scene.pending;
        if((descriptor.words[14]&0x3000)!=0x2000)return false;
        candidates.push_back(descriptor);
    }
    if(future)
    {
        if(future->size()>16384)return false;
        for(const auto &descriptor:*future)
        {
            if(!(descriptor.id&0x80000000) || !seen.insert(descriptor.id).second)return false;
            candidates.push_back(descriptor);++scene.future;
        }
    }
    const std::array<Float,3> depth_row={{Float::load(matrix[6]),Float::load(matrix[7]),Float::load(matrix[8])}};
    for(const auto &descriptor:candidates)
    {
        const auto &object=descriptor.words;const uint32_t owner=descriptor.id;
        // Unsupported transform/deformed/clipped codecs stay explicit. These
        // are branch flags, not model or track allowlists.
        if(object[14]&0x8e3){++scene.unsupported;continue;}
        // Reject out-of-range objects before constructing all nine transform
        // elements. Preserve exactly the center's C31 store/reload boundary.
        std::array<Float,3> delta;
        for(unsigned i=0;i<3;++i)delta[i]=Float::load(object[1+i])-Float::load(camera[i]);
        const int32_t depth=scenery::dot(delta,depth_row.data()).reload().fix();
        const uint32_t address=usa_model::select_model(object,depth);
        if(!address)return false;
        const uint32_t radius=read(address);
        if(int64_t(depth)-radius<1000){++scene.near;continue;}
        if(int64_t(depth)-radius>far){++scene.far;continue;}
        const bool compact=usa_model::compact_dispatch(object[14],mode,enabled);
        usa_model::Transform transform;
        if(!usa_model::prepare(object,camera,matrix,billboard,compact_billboard,
            compact,compact?read(0x54):Float::integer(200).store(),transform))return false;
        usa_model::Model loaded;
        const usa_model::Model *selected=nullptr;
        if(cache)selected=cache->get(read,address);
        else if(usa_model::load(read,address,loaded))selected=&loaded;
        if(!selected)return false;
        const auto &model=*selected;
        std::vector<usa_model::Vertex> projected;
        if(!usa_model::project(model,transform,[&](int32_t index)
            {return read(uint32_t(int64_t(usa_distance::reciprocal_base)+index));},projected,
            usa_model::Projection::host,far)){++scene.projection;continue;}
        const bool direct=bool(object[14]&0x400);
        if(!direct)for(const auto &polygon:model.polygons)
            if(!ram_span(palette_table+(polygon[0]>>16),1))return false;
        Object output;output.id=owner;output.model=address;output.depth=depth;
        if(!usa_model::quads(model,projected,direct,[&](uint32_t flags)
            {return direct?object[16]:read(palette_table+(flags>>16));},output.quads))return false;
        ++scene.decoded;scene.objects.push_back(std::move(output));
    }
    std::sort(scene.objects.begin(),scene.objects.end(),[](const Object &a,const Object &b)
        {return a.depth!=b.depth?a.depth>b.depth:a.id<b.id;});
    result=std::move(scene);return true;
}
} }
