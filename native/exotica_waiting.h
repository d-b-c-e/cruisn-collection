// SPDX-License-Identifier: BSD-3-Clause
// Owned allocated Exotica sources before their first original model submission.
// Eligibility only: no material ownership, fade handover, GPU or guest writes.
#pragma once
#include "exotica_future_sections.h"
#include "scenery_lifetimes.h"
#include <set>

namespace cruisn { namespace exotica_waiting {
struct Item {
    exotica_future::Source source;
    scenery_lifetimes::Handle owner;
};
struct Result {
    std::vector<Item> items;
    size_t historical=0,unowned=0,submitted=0,future=0,bound_future=0,bound_future_submitted=0;
};
inline bool slot(uint32_t p) {
    const uint64_t end=uint64_t(p)+31;
    return p>=0x1000 && end<=0x40000 && (end<=0x30000 || p>=0x32000);
}
inline bool immutable(unsigned i) {
    return (i>=1 && i<=3) || (i>=5 && i<=13) || i==17 || i==18 || i==19 || i==21 || i==29;
}
// Read must provide one coherent current RAM boundary. Registry observation must
// cover all allocations/removals/reset events up to that SAME boundary. Output
// retains original descriptor order. No lookup failure invents an owner.
template<class Read>
bool select(const std::vector<exotica_future::Source> &sources,uint64_t realm,
    const scenery_lifetimes::Registry &registry,Read read,Result &result)
{
    if(sources.size()>32768 || !registry.epoch() || (realm>>32)<1 || (realm>>32)>3 ||
        !exotica_future::span(uint32_t(realm),1))return false;
    Result out;std::set<std::pair<uint32_t,uint32_t>> seen;std::set<uint32_t> slots;
    const uint32_t mode=read(0x75);
    for(const auto &source:sources) {
        if(!source.supported)continue;
        if(!exotica_future::span(source.entry,4) || !exotica_future::span(source.source,6) ||
            !seen.emplace(source.entry,source.source).second)return false;
        scenery_lifetimes::Key key;key.realm=realm;key.section=source.entry;key.source=source.source;
        scenery_lifetimes::Handle handle;scenery_lifetimes::State state;
        const bool bound=registry.lookup(key,handle);
        if(bound && (!registry.inspect(handle,state) || !slot(handle.slot)))return false;
        if(source.future) {
            ++out.future;out.bound_future+=bound;
            out.bound_future_submitted+=bound && state.last_submission!=0;
            continue; // Existing future selection remains a separate policy.
        }
        ++out.historical;
        if(!bound){++out.unowned;continue;}
        if(state.last_submission){++out.submitted;continue;}
        if(out.items.size()>=4096 || !slots.insert(handle.slot).second)return false;
        Item item;item.source=source;item.owner=handle;
        for(unsigned i=0;i<31;++i) {
            const uint32_t value=read(handle.slot+i);
            if(immutable(i) && value!=source.words[i])return false;
            item.source.words[i]=value;
        }
        item.source.words[31]=0;
        item.source.words[15]&=~uint32_t((mode&0x100)?0:0x400);
        // The DTO retains future=false: eligibility is represented by this Item,
        // never by rewriting historical game/source state to appear unallocated.
        out.items.push_back(std::move(item));
    }
    result=std::move(out);return true;
}
} }
