// license:BSD-3-Clause
// Host-owned World 2.4 pending scenery. No guest memory writes or game execution.
#pragma once
#include "scenery_c31.h"
#include "world_distance.h"
#include <algorithm>
#include <vector>

namespace cruisn { namespace world_host {
using scenery::Float;
using scenery::dot;
using Quad=std::array<uint16_t,16>;
// Stable ordered little-endian FNV-1a fingerprint, also checked independently
// from detailed CSV traces. A diagnostic receipt, not a cryptographic identity.
constexpr uint64_t hash_seed=UINT64_C(14695981039346656037);
inline uint64_t quad_hash(uint64_t hash,const Quad &quad)
{
    for(auto word:quad)for(unsigned shift=0;shift<16;shift+=8)
        hash=(hash^uint8_t(word>>shift))*UINT64_C(1099511628211);
    return hash;
}
struct Object
{
    uint32_t id=0,model=0,section=0;
    int32_t depth=0;
    std::vector<Quad> quads;
};
struct Scene
{
    uint32_t pending=0,unsupported=0,distance=0,decoded=0;
    std::vector<Object> objects;
};
inline bool pointer(uint32_t p,uint32_t n)
// Static geometry/materials must reside in the mapped ROM region. A corrupt
// pointer must never make this read-only adapter touch side-effecting I/O.
{return p>=0xc00000 && n<=4096 && uint64_t(p)+n<=0x1000000;}

template<class Read> bool build(Read read,Scene &scene,uint32_t far=80000)
{
    if(far!=80000 && far!=160000 && far!=240000)return false;
    // The caller guards the exact code, ROM revision and scene boundary.
    uint32_t cam=read(0x41),view=read(0x43),bill=read(0x48),origin=read(0x47)+2;
    uint32_t head=read(0x61ec),table=read(0x4d);
    if(!head)return true;
    if(cam>=0x20000-3 || view<0x809800 || view>0x809ff7 ||
       bill<0x809800 || bill>0x809ff7 || origin<0x809800 || origin>0x809ffe ||
       head<0x1000 || head>=0x20000 || table!=0xb66f)return false;
    std::array<Float,3> camera;
    std::array<Float,9> camera_matrix,billboard;
    for(int i=0;i<3;++i)camera[i]=Float::load(read(cam+i));
    for(int i=0;i<9;++i){camera_matrix[i]=Float::load(read(view+i));billboard[i]=Float::load(read(bill+i));}
    Float ox=Float::load(read(origin)),oy=Float::load(read(origin+1));
    const Float yscale=Float::load(0x00052000);
    uint32_t id=read(head);
    std::vector<uint32_t> seen;
    while(id)
    {
        if(id<0x1000 || id>0x20000-32 || seen.size()>=2048 ||
            std::find(seen.begin(),seen.end(),id)!=seen.end())return false;
        seen.push_back(id);++scene.pending;
        std::array<uint32_t,32> obj;
        for(int i=0;i<32;++i)obj[i]=read(id+i);
        uint32_t object_id=id;id=obj[0];
        // The pending flag proves list membership; alternate road/car codecs
        // (including dynamic bit 0) are explicitly excluded, not guessed.
        if((obj[14]&0x3000)!=0x2000)return false;
        if(obj[14]&0x861){++scene.unsupported;continue;}
        std::array<Float,3> delta,center;
        for(int i=0;i<3;++i)delta[i]=Float::load(obj[i+1])-camera[i];
        for(int i=0;i<3;++i)center[i]=dot(delta,&camera_matrix[i*3]);
        int32_t depth=center[2].fix();
        for(auto &v:center)v=v.reload();
        uint32_t model=obj[13];
        if(!pointer(model,3))return false;
        if((obj[14]&0x200) && depth>10000)
        {
            const uint32_t preceding=(obj[14]&4) && depth>15000 ? 4 : 3;
            if(!pointer(obj[13]-preceding,preceding))return false;
            model=read(obj[13]-3);
            if((obj[14]&4) && depth>15000)model=read(obj[13]-4);
        }
        if(!pointer(model,3))return false;
        uint32_t radius=read(model),materials=read(model+1),header=read(model+2);
        if(int64_t(depth)-radius<1000 || int64_t(depth)+radius>=far){++scene.distance;continue;}
        uint32_t pairs=(header&0x300)?((header>>10)&255)+1:0;
        uint32_t singles=header&255,polygons=(header>>18)+1,vertices=singles+2*pairs;
        if(!vertices || vertices>256 || polygons>1024 ||
            !pointer(model,3+2*(pairs+singles)+2*polygons) || !pointer(materials,3*polygons))return false;
        std::array<Float,9> matrix;
        if(obj[14]&8)matrix=billboard;
        else
        {
            for(int col=0;col<3;++col)
            {
                std::array<Float,3> column;
                for(int k=0;k<3;++k)column[k]=Float::load(obj[4+col+k*3]);
                for(int row=0;row<3;++row)matrix[row*3+col]=dot(column,&camera_matrix[row*3]).reload();
            }
        }
        std::vector<std::array<Float,3>> projected;
        bool projection_ok=true;
        auto screen=[&](Float x,Float y,Float z)
        {
            int32_t index=z.fix()>>4;
            if(index < -80 || index>int32_t(cruisn::world_distance::maximum_index(far))){projection_ok=false;return;}
            Float r=Float::load(index<5000?read(uint32_t(int64_t(table)+index)):
                cruisn::world_distance::reciprocal(uint32_t(index),far));
            Float sx=(x*r+ox).reload(),sy=((y*r)*yscale+oy).reload();
            if(sx.fix()<-32768 || sx.fix()>32767 || sy.fix()<-32768 || sy.fix()>32767)
            {projection_ok=false;return;}
            projected.push_back({{sx,sy,z.reload()}});
        };
        int axis=int((header>>8)&3)-1;
        for(uint32_t i=0;i<pairs+singles;++i)
        {
            uint32_t xy=read(model+3+2*i),second=read(model+4+2*i);
            std::array<Float,3> local={{Float::integer(int16_t(xy)),Float::integer(int16_t(xy>>16)),
                Float::integer(i<pairs?int32_t(int16_t(second>>16)):int32_t(second))}};
            Float x=dot(local,&matrix[0]).reload()+center[0];
            Float y=dot(local,&matrix[3])+center[1],z=dot(local,&matrix[6])+center[2];
            screen(x,y,z);
            if(i<pairs)
            {
                Float offset=Float::integer(second&65535);
                screen(offset*matrix[axis]+x.reload(),offset*matrix[axis+3]+y.reload(),offset*matrix[axis+6]+z.reload());
            }
        }
        if(!projection_ok){++scene.distance;continue;}
        if(projected.size()!=vertices)return false;
        Object object;object.id=object_id;object.model=model;object.depth=depth;object.section=obj[27]&65535;
        uint32_t poly_start=model+3+2*(pairs+singles);
        for(uint32_t i=0;i<polygons;++i)
        {
            uint32_t flags=read(poly_start+2*i),packed=read(poly_start+2*i+1);
            uint32_t ix[4]={(packed&255),(packed>>8)&255,(packed>>16)&255,(packed>>24)&255};
            for(auto j:ix)if(j>=vertices)return false;
            const auto &a=projected[ix[0]],&b=projected[ix[1]],&c=projected[ix[2]];
            Float cross=(b[1]-c[1])*(b[0]-a[0])-(b[0]-c[0])*(b[1]-a[1]);
            if(cross.e!=-128 && cross.m>=0)continue;
            Quad quad{};quad[0]=uint16_t(flags);quad[1]=uint16_t(obj[16]);
            for(int j=0;j<4;++j){quad[2+2*j]=uint16_t(projected[ix[j]][0].fix());quad[3+2*j]=uint16_t(projected[ix[j]][1].fix());}
            uint32_t uv0=read(materials+3*i),uv1=read(materials+3*i+1),tex=read(materials+3*i+2);
            quad[10]=uint16_t(uv0);quad[11]=uint16_t(uv0>>16);quad[12]=uint16_t(uv1);quad[13]=uint16_t(uv1>>16);
            quad[14]=uint16_t(tex+obj[17]);object.quads.push_back(quad);
        }
        ++scene.decoded;scene.objects.push_back(std::move(object));
    }
    std::sort(scene.objects.begin(),scene.objects.end(),[](const Object &a,const Object &b)
        {return a.depth!=b.depth?a.depth>b.depth:a.id<b.id;});
    return true;
}
} }
