// SPDX-License-Identifier: BSD-3-Clause
// Private draw admission carried through later guest source allocation.
// Caller supplies only successfully queued nonempty draws, observes every source
// bind/release/reset, and copies qualification into the original command ticket.
// This ledger proves submission history, not screen visibility or a fade policy.
#pragma once
#include "scenery_lifetimes.h"
#include <set>
#include <vector>
namespace cruisn { namespace exotica_admissions {
using scenery_lifetimes::Key;
using scenery_lifetimes::Handle;
struct Draw {Key key;uint32_t quads=0;};
struct Entry {
    Key key;Handle owner;
    uint64_t epoch=0,first_sequence=0,last_sequence=0;
    uint32_t first_frame=0,last_frame=0;
    bool bound=false;
};
enum class Status {invalid,unadmitted,matched};
inline bool same(const Handle &a,const Handle &b) {
    return a.slot==b.slot && a.epoch==b.epoch && a.generation==b.generation && a.key==b.key;
}
inline bool valid(const Handle &h) {
    return h.key.valid() && h.epoch && h.generation && h.slot;
}
class Ledger {
    std::map<Key,Entry> m_entries;
    uint64_t m_epoch=0,m_sequence=0;
    uint32_t m_frame=0;
public:
    size_t size()const{return m_entries.size();}
    uint64_t epoch()const{return m_epoch;}
    bool reset(uint64_t epoch) {
        if(!epoch || epoch<=m_epoch)return false;
        m_entries.clear();m_epoch=epoch;m_sequence=0;m_frame=0;return true;
    }
    // One sequence per successfully queued private packet; waiting and future
    // packets may share a scene/frame but have distinct submission sequences.
    bool admit(uint64_t sequence,uint32_t frame,const std::vector<Draw> &draws,
               const scenery_lifetimes::Registry &registry) {
        if(!m_epoch || registry.epoch()!=m_epoch || !sequence || sequence<=m_sequence ||
                !frame || frame<m_frame || draws.size()>32768)return false;
        std::set<Key> seen;std::vector<Entry> prepared;size_t added=0;
        prepared.reserve(draws.size());
        for(const auto &draw:draws) {
            if(!draw.key.valid() || !draw.quads || draw.quads>131072 || !seen.insert(draw.key).second)return false;
            Handle owner;const bool bound=registry.lookup(draw.key,owner);
            const auto found=m_entries.find(draw.key);Entry e;
            if(found==m_entries.end()) {
                ++added;e.key=draw.key;e.epoch=m_epoch;e.first_sequence=sequence;e.first_frame=frame;
                e.bound=bound;if(bound)e.owner=owner;
            } else {
                e=found->second;
                // Never silently repair a missed binding/removal using today's
                // slot occupant: that would hide a source-generation reuse.
                if(e.bound!=bound || (bound && !same(e.owner,owner)))return false;
            }
            e.last_sequence=sequence;e.last_frame=frame;prepared.push_back(e);
        }
        if(added>32768-m_entries.size())return false;
        for(const auto &e:prepared)m_entries[e.key]=e;
        m_sequence=sequence;m_frame=frame;return true;
    }
    Status bind(const Handle &owner) {
        if(!valid(owner) || owner.epoch!=m_epoch)return Status::invalid;
        auto found=m_entries.find(owner.key);if(found==m_entries.end())return Status::unadmitted;
        if(found->second.bound)return Status::invalid;
        found->second.owner=owner;found->second.bound=true;return Status::matched;
    }
    Status release(const Handle &owner) {
        if(!valid(owner) || owner.epoch!=m_epoch)return Status::invalid;
        auto found=m_entries.find(owner.key);if(found==m_entries.end())return Status::unadmitted;
        if(!found->second.bound || !same(found->second.owner,owner))return Status::invalid;
        m_entries.erase(found);return Status::matched;
    }
    Status qualify(const Handle &owner,Entry &output)const {
        if(!valid(owner) || owner.epoch!=m_epoch)return Status::invalid;
        const auto found=m_entries.find(owner.key);if(found==m_entries.end())return Status::unadmitted;
        if(!found->second.bound || !same(found->second.owner,owner))return Status::invalid;
        output=found->second;return Status::matched;
    }
};
} }
