// SPDX-License-Identifier: BSD-3-Clause
// Reconcile a derived waiting cohort with original submissions/removals.
// Selection only: callers still prove the actual scene/device fence, materials,
// camera/page ownership and alpha/command order before drawing any retained item.
#pragma once
#include "exotica_waiting.h"

namespace cruisn { namespace exotica_waiting {
struct Completion {
    std::vector<Item> items;
    size_t captured=0,submitted=0,retired=0;
};
class Pending {
    Result m_selection;
    uint64_t m_epoch=0,m_sequence=0,m_records=0;
public:
    bool pending() const { return m_epoch!=0; }
    const Result &selection() const { return m_selection; }
    void cancel() { m_selection=Result{};m_epoch=0;m_sequence=0;m_records=0; }

    // Always derive the cohort through the canonical registry/source selector;
    // there is no API for substituting a caller-supplied list of object handles.
    // records is the adapter's actual observation watermark, including bindings
    // and submissions: the registry's pool sequence alone does not count those.
    template<class Read>
    bool capture(const std::vector<exotica_future::Source> &sources,uint64_t realm,
        const scenery_lifetimes::Registry &registry,uint64_t records,Read read)
    {
        if(pending() || !records)return false;
        Result selected;
        if(!select(sources,realm,registry,read,selected))return false;
        m_selection=std::move(selected);m_epoch=registry.epoch();m_sequence=registry.sequence();m_records=records;
        return true;
    }

    // Keep the immutable proposal DTOs and their source order. A later object
    // allocation cannot inherit an earlier slot's geometry or material identity.
    // Reset/order errors fail the complete proposal rather than guessing a view.
    bool complete(const scenery_lifetimes::Registry &registry,uint64_t records,Completion &result)
    {
        if(!pending() || records<m_records || registry.epoch()!=m_epoch || registry.sequence()<m_sequence)return false;
        Completion out;out.captured=m_selection.items.size();
        for(const auto &item:m_selection.items) {
            scenery_lifetimes::State state;
            if(!registry.inspect(item.owner,state)) {++out.retired;continue;}
            if(state.last_submission) {++out.submitted;continue;}
            out.items.push_back(item);
        }
        result=std::move(out);cancel();return true;
    }
};
} }
