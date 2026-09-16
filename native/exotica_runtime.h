// SPDX-License-Identifier: BSD-3-Clause
// Continuous operation is explicit; capture intervals retain their old meaning.
#pragma once
#include "exotica_journal_policy.h"
#include <cstdint>
#include <limits>

namespace cruisn { namespace exotica_runtime {
enum class Policy { capture, continuous };
template<class Lookup>
bool select(const char *mode,Lookup lookup,Policy &policy) {
    policy=Policy::capture;
    if(!mode)return true;
    if(std::strcmp(mode,"continuous"))return false;
    DiagnosticJournal::Policy journal;
    if(!exotica_journals::select(lookup("MIDZ_HOST_JOURNALS"),lookup,journal) ||
        journal!=DiagnosticJournal::Policy::quiet)return false;
    const char *required[][2]={{"MIDZ_BOOTSTRAP","3"},{"MIDZ_SHUTDOWN_OBSERVE","1"},{"MIDZ_DEPTH_FIRST","2"}};
    for(const auto &entry:required) {
        const char *value=lookup(entry[0]);
        if(!value || std::strcmp(value,entry[1]))return false;
    }
    policy=Policy::continuous;return true;
}
inline bool continuous(Policy policy) {return policy==Policy::continuous;}
// Fault injection is a bounded diagnostic even when real runtime is continuous.
// Guest-based startup can prepare a scene before the old capture first frame.
inline uint32_t failure_first(bool scene_bootstrap,uint32_t capture_first) {
    return scene_bootstrap ? 1 : capture_first;
}
inline uint32_t injection_last(Policy policy,uint32_t capture_last) {
    return continuous(policy) ? 16000 : capture_last;
}
// Frames travel on existing 32-bit packets. Never silently wrap at narrowing.
inline bool representable(uint64_t frame) {return frame<=std::numeric_limits<uint32_t>::max();}
// Real recovery is not fault injection: a continuous session may fail after the
// diagnostic injection window. Keep the old bounded capture protocol unchanged.
inline bool retirement_frame(Policy policy,uint64_t frame) {
    return frame>=1 && representable(frame) && (continuous(policy) || frame<=16000);
}
inline bool after(Policy policy,uint64_t frame,uint32_t last) {
    return !continuous(policy) && frame>last;
}
inline bool within(Policy policy,uint64_t frame,uint32_t first,uint32_t last) {
    return representable(frame) && frame>=first && !after(policy,frame,last);
}
// Zero explicitly disables routine operands only under qualified quiet runtime.
// Capture trials retain their selected-frame contract; first failures survive.
inline bool endpoint_snapshot_allowed(Policy policy,uint32_t snapshot,uint32_t first,uint32_t last) {
    return snapshot ? first<=snapshot && snapshot<=last : continuous(policy);
}
inline bool capture_endpoint(uint32_t frame,uint32_t snapshot,unsigned prepared,bool marked,uint64_t rejected) {
    return (snapshot && frame==snapshot && prepared) || (marked && prepared==2 && rejected==1);
}
}}
