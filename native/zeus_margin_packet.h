// SPDX-License-Identifier: BSD-3-Clause
// owned private materials plus checked, margin-only D24 geometry.
#pragma once
#include "zeus_host_materials.h"
#include "zeus_model.h"
#include <cstring>

namespace cruisn { namespace zeus_margin {
struct Quad { zeus_model::Quad polygon; uint32_t palette=0; };
struct Packet {
    zeus_host::Packet materials;
    uint32_t margin=0,page=0;
    bool draw=false;
    std::vector<Quad> quads;
};
constexpr size_t header_bytes=32,quad_bytes=264,max_quads=131072;
constexpr size_t maximum_bytes=header_bytes+zeus_host::maximum_material_bytes+max_quads*quad_bytes;
static_assert(maximum_bytes+8<(64u<<20),"private margin scene exceeds native queue");

// This diagnostic deliberately retains original D24 math. A whole instance
// that cannot satisfy this contract must be counted/excluded before packaging,
// never silently saturated or accepted as general far-distance rendering.
inline bool depth24(const zeus_model::Quad &q,uint32_t frame,uint32_t page) {
    const auto &s=q.state;const uint32_t flags=s[9];
    if(s[0]!=frame || s[1]<3 || s[1]>8 || s[11]!=page || s[12] ||
        (page!=0 && page!=400) || s[13]!=0 || s[15]!=511 || s[14]>s[16] || s[16]>399 ||
        !(flags&8) || (flags&~uint32_t(0x2df)) || s[7]>256 || s[8]>256)return false;
    const auto bias=int32_t(s[10]);
    for(unsigned i=0;i<s[1];++i) {
        const auto &v=q.vertices[i];
        for(float f:v)if(!std::isfinite(f))return false;
        if(v[5]<=0 || v[2]<0 || v[2]>16777215.f)return false;
        // Convex interpolation stays within these endpoint bounds. Use double
        // to check the shader's integer add without a host overflow.
        const double z=(flags&4)?((flags&512)?std::max(double(v[2]),double(bias)):double(v[2])+bias):double(v[2]);
        if(z<0 || z>16777215.)return false;
    }
    return true;
}
inline bool shape(const Packet &p) {
    if(p.margin>120 || (p.page!=0 && p.page!=400) || p.quads.size()>max_quads)return false;
    for(const auto &q:p.quads)
        if(q.palette>=p.materials.rows.size() || !depth24(q.polygon,p.materials.frame,p.page))return false;
    return true;
}
inline bool encode(const Packet &p,std::vector<uint8_t> &out) {
    if(!shape(p))return false;
    std::vector<uint8_t> material,wire;
    if(!zeus_host::encode(p.materials,material))return false;
    wire.reserve(header_bytes+material.size()+p.quads.size()*quad_bytes);
    using zeus_host::put32;
    put32(wire,0x31444d58); //XMD1: no borrowed original material rows or pointers
    put32(wire,uint32_t(material.size()));put32(wire,uint32_t(p.quads.size()));
    put32(wire,p.margin);put32(wire,p.page);put32(wire,p.draw?1:0);
    put32(wire,0);put32(wire,0);
    wire.insert(wire.end(),material.begin(),material.end());
    for(const auto &q:p.quads) {
        put32(wire,q.palette);
        for(auto value:q.polygon.state)put32(wire,value);
        for(const auto &v:q.polygon.vertices)for(float f:v) {
            uint32_t word;std::memcpy(&word,&f,4);put32(wire,word);
        }
    }
    out=std::move(wire);return true;
}
inline bool decode(const uint8_t *wire,size_t size,Packet &out) {
    using zeus_host::get32;
    if(!wire || size<header_bytes || size>maximum_bytes || get32(wire)!=0x31444d58 ||
        get32(wire+20)>1 || get32(wire+24) || get32(wire+28))return false;
    const uint32_t material=get32(wire+4),count=get32(wire+8);
    if(material>zeus_host::maximum_material_bytes || count>max_quads ||
        size!=header_bytes+size_t(material)+size_t(count)*quad_bytes)return false;
    Packet p;p.margin=get32(wire+12);p.page=get32(wire+16);p.draw=get32(wire+20)!=0;
    if(!zeus_host::decode(wire+header_bytes,material,p.materials))return false;
    p.quads.reserve(count);const auto *data=wire+header_bytes+material;
    for(unsigned i=0;i<count;++i) {
        Quad q;q.palette=get32(data);data+=4;
        for(auto &value:q.polygon.state){value=get32(data);data+=4;}
        for(auto &v:q.polygon.vertices)for(float &f:v) {
            const uint32_t word=get32(data);data+=4;std::memcpy(&f,&word,4);
        }
        p.quads.push_back(q);
    }
    if(!shape(p))return false;
    out=std::move(p);return true;
}
} }
