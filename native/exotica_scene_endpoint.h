// SPDX-License-Identifier: BSD-3-Clause
// Apply a prepared private endpoint AFTER filtering original geometry. The
// caller establishes source permission, scene/page/material ownership and the
// actual draw boundary. This helper cannot certify any of those live facts.
#pragma once
#include "exotica_composition.h"
#include "zeus_endpoint_pair.h"

namespace cruisn { namespace exotica_scene_endpoint {
// Both full scenes must have identical ordered instances and vertices. Retained
// must be an ordered, exact original subset (for example the composition output).
// Never compare completed alpha to decide whether two original copies match:
// completing a fade could conceal a real original-state difference.
inline bool select(const exotica_scene::Result &original,
    const exotica_scene::Result &endpoint,const exotica_scene::Result &retained,
    bool active,exotica_scene::Result &result)
{
    using exotica_composition::layout;
    using exotica_composition::same_render;
    if(!layout(original,active) || !layout(endpoint,active) || !layout(retained,active) ||
        original.instances.size()!=endpoint.instances.size() ||
        original.quads.size()!=endpoint.quads.size())return false;
    for(size_t i=0;i<original.instances.size();++i) {
        const auto &a=original.instances[i],&b=endpoint.instances[i];
        if(a.entry!=b.entry || a.source!=b.source || a.first_quad!=b.first_quad || !same_render(a,b))return false;
        for(size_t j=0;j<a.quad_count;++j) {
            zeus_endpoint_pair::Pair pair;
            pair.original=original.quads[a.first_quad+j];pair.replacement=endpoint.quads[b.first_quad+j];
            pair.frame=pair.original.state[0];pair.model=uint32_t(i+1);
            pair.index=uint32_t(j);pair.count=uint32_t(a.quad_count);
            if(!zeus_endpoint_pair::valid(pair))return false;
        }
    }
    exotica_scene::Result selected=retained;size_t cursor=0;
    for(const auto &r:retained.instances) {
        while(cursor<original.instances.size() &&
            (original.instances[cursor].entry!=r.entry || original.instances[cursor].source!=r.source))++cursor;
        if(cursor==original.instances.size())return false;
        const auto &a=original.instances[cursor],&b=endpoint.instances[cursor];
        if(!same_render(a,r))return false;
        for(size_t j=0;j<r.quad_count;++j) {
            const auto &x=original.quads[a.first_quad+j],&y=retained.quads[r.first_quad+j];
            if(std::memcmp(&x,&y,sizeof(x)))return false;
            selected.quads[r.first_quad+j]=endpoint.quads[b.first_quad+j];
        }
        ++cursor;
    }
    result=std::move(selected);return true;
}
} }
