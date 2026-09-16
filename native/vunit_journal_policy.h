// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include "diagnostic_journal.h"
#include "vunit_runtime.h"
namespace cruisn { namespace vunit_journals {
template<class Lookup> bool select(const char *mode,Lookup lookup,DiagnosticJournal::Policy &policy)
{
    policy=DiagnosticJournal::Policy::capture;
    if(!mode)return true;
    vunit_runtime::Policy runtime;
    const char *selected=lookup("MIDV_HOST_RUNTIME");
    if(std::strcmp(mode,"quiet") || !selected ||
            !vunit_runtime::select(selected,lookup,runtime) || !vunit_runtime::continuous(runtime))return false;
    for(const auto *key:{"MIDV_WORLD_HOST_QUADS","MIDV_USA_HOST_QUADS","MIDV_OFFROAD_HOST_QUADS",
            "MIDV_WORLD_HOST_FADE_METADATA","MIDV_GL_ORIGINAL_MIRROR"}) {
        const char *value=lookup(key);if(value && std::strcmp(value,"0"))return false;
    }
    // World defaults to detailed capture. Quiet requires an explicit summary.
    const char *world=lookup("MIDV_WORLD_HOST_SCENERY");
    if(world && std::strcmp(world,"0")) {
        const char *quads=lookup("MIDV_WORLD_HOST_QUADS");
        if(!quads || std::strcmp(quads,"0"))return false;
    }
    policy=DiagnosticJournal::Policy::quiet;return true;
}
// Fixed LE64 fields: frame, page, quad count, ordered quad fingerprint.
// This is geometry evidence, not proof of all source/material semantics.
inline uint64_t fold(uint64_t hash,uint64_t frame,uint64_t page,uint64_t quads,uint64_t geometry)
{
    for(uint64_t word:{frame,page,quads,geometry})for(unsigned byte=0;byte<8;++byte) {
        hash^=uint8_t(word>>(8*byte));hash*=1099511628211ull;
    }
    return hash;
}
constexpr uint64_t seed=14695981039346656037ull;
}}
