// SPDX-License-Identifier: BSD-3-Clause
// Remove active-margin copies already present in a completed waiting draw.
// The caller MUST establish the actual shared scene/camera/page/device boundary,
// validate owner lifetimes through that boundary, and retain the proposal image.
// This helper compares owned render data; it cannot establish those live facts.
#pragma once
#include "exotica_scene.h"
#include "zeus_resource_lease.h"
#include "scenery_lifetimes.h"

namespace cruisn { namespace exotica_composition {
struct Counts {size_t overlaps=0,removed_quads=0,texture_pages=0;};
inline bool layout(const exotica_scene::Result &scene,bool active) {
    if(scene.instances.size()>exotica_scene::max_instances || scene.quads.size()>exotica_scene::max_quads)return false;
    size_t next=0;std::set<std::pair<uint32_t,uint32_t>> keys;std::set<uint32_t> slots;
    for(const auto &i:scene.instances) {
        if(!i.entry || !i.source || !keys.emplace(i.entry,i.source).second ||
            (active && !slots.insert(i.source).second) || i.first_quad!=next ||
            i.quad_count>scene.quads.size()-next)return false;
        next+=i.quad_count;
    }
    return next==scene.quads.size();
}
inline bool same_render(const exotica_scene::Instance &a,const exotica_scene::Instance &b) {
    return std::tie(a.descriptor,a.base,a.count,a.band,a.palette,a.palette_control,a.depth,a.quad_count)==
           std::tie(b.descriptor,b.base,b.count,b.band,b.palette,b.palette_control,b.depth,b.quad_count);
}

// Owners are the already reconciled native cohort, not a guessed slot match.
// Any ambiguous overlap rejects the entire result before changing either output.
// Keep waiting alpha/order untouched and preserve the remaining active order.
inline bool filter(const exotica_scene::Result &active,const exotica_scene::Result &waiting,
    const std::vector<scenery_lifetimes::Handle> &owners,const uint8_t *proposal,
    const uint8_t *ready,size_t bytes,exotica_scene::Result &result,Counts &counts)
{
    if(!layout(active,true) || !layout(waiting,false) || owners.size()>4096 ||
        !proposal || !ready || bytes!=zeus_lease::wave_bytes)return false;
    using Key=std::pair<uint32_t,uint32_t>;
    std::map<Key,uint32_t> slots;std::set<uint32_t> unique_slots;
    uint64_t realm=0,epoch=0;
    for(const auto &h:owners) {
        if(!h.slot || !h.epoch || !h.generation || !h.key.valid() ||
            (realm && h.key.realm!=realm) || (epoch && h.epoch!=epoch) ||
            !slots.emplace(Key(h.key.section,h.key.source),h.slot).second || !unique_slots.insert(h.slot).second)return false;
        realm=h.key.realm;epoch=h.epoch;
    }
    std::map<uint32_t,const exotica_scene::Instance *> by_slot;
    for(const auto &i:waiting.instances) {
        auto found=slots.find({i.entry,i.source});if(found==slots.end())return false;
        if(!by_slot.emplace(found->second,&i).second)return false;
    }
    Counts checked;std::set<uint32_t> remove;zeus_lease::Coverage coverage;
    for(const auto &a:active.instances) {
        const auto found=by_slot.find(a.source);if(found==by_slot.end())continue;
        const auto &b=*found->second;
        if(!same_render(a,b))return false;
        for(size_t j=0;j<a.quad_count;++j) {
            const auto &x=active.quads[a.first_quad+j],&y=waiting.quads[b.first_quad+j];
            if(x.state!=y.state || std::memcmp(x.vertices.data(),y.vertices.data(),sizeof(x.vertices)) || !coverage.add(x))return false;
        }
        if(!zeus_lease::palette_equal(proposal,ready,bytes,a.palette))return false;
        remove.insert(a.source);++checked.overlaps;checked.removed_quads+=a.quad_count;
    }
    if(!coverage.equal(proposal,ready,bytes))return false;
    checked.texture_pages=coverage.count();
    exotica_scene::Result filtered=active;filtered.instances.clear();filtered.quads.clear();
    for(auto i:active.instances) {
        if(remove.count(i.source))continue;
        const auto begin=active.quads.begin()+i.first_quad;i.first_quad=filtered.quads.size();
        filtered.quads.insert(filtered.quads.end(),begin,begin+i.quad_count);filtered.instances.push_back(i);
    }
    result=std::move(filtered);counts=checked;return true;
}
} }
