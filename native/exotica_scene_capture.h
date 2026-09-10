// SPDX-License-Identifier: BSD-3-Clause
// Local-only scene evidence serialization. Contains no game resources.
#pragma once
#include "exotica_scene.h"
namespace cruisn { namespace exotica_scene {
template<class Values> void append_words(std::vector<uint32_t> &out,const Values &values)
{out.insert(out.end(),values.begin(),values.end());}
inline std::vector<uint32_t> parameter_words(const Parameters &p,uint32_t bank,bool partial)
{
    auto bits=[](float f){uint32_t w;std::memcpy(&w,&f,4);return w;};
    std::vector<uint32_t> out={p.frustum_bounds?0x32534358U:0x31534358U,p.frame,p.multiplier,bits(p.margin),uint32_t(p.complete_fade),
        bank,uint32_t(partial),p.scale,p.setup.palette_setup};
    append_words(out,p.camera);append_words(out,p.view);append_words(out,p.alternate);
    append_words(out,p.setup.constants);append_words(out,p.setup.commands);append_words(out,p.setup.programs);
    for(const auto &b:p.setup.bodies)append_words(out,b);
    out.push_back(uint32_t(p.setup.defaults.size()));append_words(out,p.setup.defaults);
    const auto &c=p.context;
    for(auto w:{c.quad_size,c.ucode,c.palette,c.texture,c.yscale,c.zoffset})out.push_back(w);
    for(auto f:c.matrix)out.push_back(bits(f));
    for(auto f:c.translation)out.push_back(bits(f));
    for(auto f:c.light)out.push_back(bits(f));
    append_words(out,c.regs);append_words(out,c.render);
    if(p.frustum_bounds)out.push_back(1);
    return out;
}
inline std::vector<std::array<uint32_t,11>> instance_words(const Result &scene)
{
    std::vector<std::array<uint32_t,11>> out;
    for(const auto &s:scene.instances)out.push_back({{s.entry,s.source,s.descriptor,s.base,s.count,s.band,s.palette,s.palette_control,
        uint32_t(s.depth),uint32_t(s.first_quad),uint32_t(s.quad_count)}});
    return out;
}
inline uint64_t byte_hash(const void *data,size_t bytes)
{
    uint64_t h=UINT64_C(14695981039346656037);const auto *p=static_cast<const uint8_t *>(data);
    for(size_t i=0;i<bytes;++i){h^=p[i];h*=UINT64_C(1099511628211);}return h;
}
} }
