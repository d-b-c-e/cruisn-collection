// SPDX-License-Identifier: BSD-3-Clause
// Bounded host identity for reused guest object slots. No guest reads/writes,
// culling, materials, rendering or opacity policy. The adapter must observe the
// actual allocator, removal and reset transactions before calling this helper.
#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <tuple>
#include <utility>

namespace cruisn { namespace scenery_lifetimes {
struct Key {
    uint64_t realm=0; // adapter-owned track/bank identity, not a RAM slot
    uint32_t section=0,source=0;
    bool valid()const{return realm && section && source;}
    bool operator<(const Key &b)const{return std::tie(realm,section,source)<std::tie(b.realm,b.section,b.source);}
    bool operator==(const Key &b)const{return realm==b.realm && section==b.section && source==b.source;}
};
struct Layout {
    // Inclusive bounds on valid object START addresses. Some guest allocators
    // adopt externally created objects into their free lists; a contiguous
    // stride is not an ownership contract. The adapter checks object extent.
    uint32_t first=0,last=0,max_tracked=0;
    bool valid()const{return first && first<=last && max_tracked && max_tracked<=4096;}
};
struct Handle {uint32_t slot=0;uint64_t epoch=0,generation=0;Key key;};
struct State {Handle handle;uint64_t last_submission=0;};
class Registry {
    enum class Life {free,live};
    struct Slot {Life life=Life::free;uint64_t generation=0,last_submission=0;bool bound=false;Key key;};
    Layout m_layout;
    std::map<uint32_t,Slot> m_slots;
    std::map<Key,uint32_t> m_sources;
    uint64_t m_sequence=0,m_epoch=0;
    bool m_unknown=false;
    bool valid_address(uint32_t address)const{return m_epoch && address>=m_layout.first && address<=m_layout.last;}
    bool next()const{return m_sequence<std::numeric_limits<uint64_t>::max();}
    Handle handle(uint32_t address,const Slot &s)const {
        Handle h;h.slot=address;h.epoch=m_epoch;h.generation=s.generation;h.key=s.key;return h;
    }
public:
    uint64_t sequence()const{return m_sequence;}
    uint64_t epoch()const{return m_epoch;}
    size_t bound_sources()const{return m_sources.size();}
    // Unknown permits observing a recording after earlier allocations. A free
    // of such a slot is explicit in its result, never assigned a fake generation.
    bool start(const Layout &layout,bool initially_unknown=true) {
        if(m_epoch || !layout.valid())return false;
        m_layout=layout;m_unknown=initially_unknown;m_epoch=1;return true;
    }
    bool reset(const Layout &layout) {
        if(!m_epoch || !layout.valid() || !next() || m_epoch==std::numeric_limits<uint64_t>::max())return false;
        m_layout=layout;m_slots.clear();m_sources.clear();m_unknown=false;++m_sequence;++m_epoch;return true;
    }
    bool allocate(uint32_t address,uint64_t &generation) {
        if(!valid_address(address) || !next())return false;
        auto found=m_slots.find(address);
        if(found==m_slots.end() ? m_slots.size()>=m_layout.max_tracked : found->second.life==Life::live)return false;
        Slot s;s.life=Life::live;s.generation=m_sequence+1;m_slots[address]=s;++m_sequence;
        generation=s.generation;return true;
    }
    bool release(uint32_t address,bool &was_unknown) {
        if(!valid_address(address) || !next())return false;
        auto found=m_slots.find(address);const bool unknown=found==m_slots.end();
        if(unknown ? (!m_unknown || m_slots.size()>=m_layout.max_tracked) : found->second.life!=Life::live)return false;
        if(!unknown && found->second.bound)m_sources.erase(found->second.key);
        Slot s;s.life=Life::free;m_slots[address]=s;++m_sequence;was_unknown=unknown;return true;
    }
    bool bind(uint32_t address,const Key &key,Handle &output) {
        if(!valid_address(address) || !key.valid())return false;
        auto found=m_slots.find(address);if(found==m_slots.end())return false;
        auto &s=found->second;if(s.life!=Life::live || s.bound || m_sources.count(key))return false;
        m_sources.emplace(key,address);s.key=key;s.bound=true;output=handle(address,s);return true;
    }
    bool lookup(const Key &key,Handle &output)const {
        const auto it=m_sources.find(key);if(it==m_sources.end())return false;
        const auto found=m_slots.find(it->second);if(found==m_slots.end())return false;
        const auto &s=found->second;if(s.life!=Life::live || !s.bound || !(s.key==key))return false;
        output=handle(it->second,s);return true;
    }
    bool inspect(const Handle &h,State &output)const {
        if(h.epoch!=m_epoch || !valid_address(h.slot))return false;
        const auto found=m_slots.find(h.slot);if(found==m_slots.end())return false;
        const auto &s=found->second;
        if(s.life!=Life::live || !s.bound || h.generation!=s.generation || !(h.key==s.key))return false;
        State state;state.handle=h;state.last_submission=s.last_submission;output=state;return true;
    }
    // A submission is an adapter-observed model/scene event, not visible pixels.
    // Same-scene repeats are legal; time reversal and stale owners reject.
    bool submitted(const Handle &h,uint64_t scene,bool &first) {
        State state;if(!scene || !inspect(h,state) || scene<state.last_submission)return false;
        auto found=m_slots.find(h.slot);if(found==m_slots.end())return false;
        first=!found->second.last_submission;found->second.last_submission=scene;return true;
    }
};
} }
