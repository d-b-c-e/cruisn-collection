// Owned future-geometry contract; separate from the legacy XMD1 margin path.
// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include "zeus_host_materials.h"
#include "zeus_model.h"
#include <cstring>

namespace cruisn { namespace zeus_wide {
constexpr float maximum_depth=67108860.f; // largest chosen depth below clear1
struct Quad { zeus_model::Quad polygon; uint32_t palette=0; };
struct Packet {
    zeus_host::Packet materials;
    uint32_t margin=0,page=0,multiplier=1;
    bool draw=false;
    std::vector<Quad> quads;
};
constexpr size_t header_bytes=32,quad_bytes=264,max_quads=131072;
static_assert(sizeof(zeus_model::Quad)==quad_bytes-4,"XWD1 polygon shape changed");
constexpr size_t maximum_bytes=header_bytes+zeus_host::maximum_material_bytes+max_quads*quad_bytes;
static_assert(maximum_bytes+8<(64u<<20),"private wide scene exceeds native queue");

// Ordinary depth-tested future geometry only. Raw writes, explicit clears and
// non-depth-tested overlays cannot enter this path. Reject out-of-range input;
// do not silently make it share the far-depth sentinel or weaken XMD1.
inline bool depth_range(const zeus_model::Quad &q,uint32_t frame,uint32_t page) {
    const auto &s=q.state;const uint32_t flags=s[9];
    if(s[0]!=frame || s[1]<3 || s[1]>8 || s[11]!=page || s[12] ||
        (page!=0 && page!=400) || s[13]!=0 || s[15]!=511 || s[14]>s[16] || s[16]>399 ||
        !(flags&8) || (flags&~uint32_t(0x2df)) || s[7]>256 || s[8]>256)return false;
    const auto bias=int32_t(s[10]);
    for(unsigned i=0;i<s[1];++i) {
        const auto &v=q.vertices[i];
        for(float f:v)if(!std::isfinite(f))return false;
        if(v[5]<=0 || v[2]<0 || v[2]>maximum_depth)return false;
        // Shader truncates p.x before its signed depth bias. Checking both
        // neighboring integer endpoints conservatively covers interpolation.
        const double low=std::floor(double(v[2])),high=std::ceil(double(v[2]));
        for(double z:{low,high}) {
            const double d=(flags&4)?((flags&512)?std::max(z,double(bias)):z+double(bias)):z;
            if(d<0 || d>double(maximum_depth))return false;
        }
    }
    return true;
}
inline bool shape(const Packet &p) {
    if(p.margin>120 || (p.page!=0 && p.page!=400) || p.multiplier<1 || p.multiplier>3 || p.quads.size()>max_quads)return false;
    for(const auto &q:p.quads)
        if(q.palette>=p.materials.rows.size() || !depth_range(q.polygon,p.materials.frame,p.page))return false;
    return true;
}
inline bool encode(const Packet &p,std::vector<uint8_t> &out) {
    if(!shape(p))return false;
    std::vector<uint8_t> material,wire;
    if(!zeus_host::encode(p.materials,material))return false;
    wire.resize(header_bytes+material.size()+p.quads.size()*quad_bytes);
    auto *data=wire.data();
    // Shape and material encoding bound the complete allocation before writes.
    // Keep the portable little-endian wire format without per-byte vector growth.
    auto put=[&](uint32_t word) {
        *data++=uint8_t(word);*data++=uint8_t(word>>8);
        *data++=uint8_t(word>>16);*data++=uint8_t(word>>24);
    };
    put(0x31445758);put(uint32_t(material.size()));put(uint32_t(p.quads.size()));
    put(p.margin);put(p.page);put(p.multiplier);put(p.draw?1:0);put(0);
    std::memcpy(data,material.data(),material.size());data+=material.size();
    for(const auto &q:p.quads) {
        put(q.palette);
        for(auto value:q.polygon.state)put(value);
        for(const auto &v:q.polygon.vertices)for(float f:v) {
            uint32_t word;std::memcpy(&word,&f,4);put(word);
        }
    }
    out=std::move(wire);return true;
}
inline bool decode(const uint8_t *wire,size_t size,Packet &out) {
    using zeus_host::get32;
    if(!wire || size<header_bytes || size>maximum_bytes || get32(wire)!=0x31445758 || get32(wire+24)>1 || get32(wire+28))return false;
    const uint32_t material=get32(wire+4),count=get32(wire+8);
    if(material>zeus_host::maximum_material_bytes || count>max_quads || size!=header_bytes+size_t(material)+size_t(count)*quad_bytes)return false;
    Packet p;p.margin=get32(wire+12);p.page=get32(wire+16);p.multiplier=get32(wire+20);p.draw=get32(wire+24)!=0;
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
