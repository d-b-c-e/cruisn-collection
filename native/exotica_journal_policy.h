// SPDX-License-Identifier: BSD-3-Clause
// Quiet is a bounded combined-renderer trial, not continuous player mode.
#pragma once
#include "diagnostic_journal.h"
#include <cstring>

namespace cruisn { namespace exotica_journals {
template<class Lookup>
bool select(const char *mode,Lookup lookup,DiagnosticJournal::Policy &policy) {
    policy=DiagnosticJournal::Policy::capture;
    if(!mode || !std::strcmp(mode,"capture"))return true;
    if(std::strcmp(mode,"quiet"))return false;
    const char *required[][2]={
        {"MIDV_FFB","0"},{"MIDZ_GL","1"},{"MIDZ_HOST_SCENE","1"},
        {"MIDZ_LIFETIME","1"},{"MIDZ_HOST_MATERIALS","1"},
        {"MIDZ_HOST_WAITING","1"},{"MIDZ_HOST_FENCE","1"},
        {"MIDZ_HOST_HANDOVER","2"},{"MIDZ_HOST_ACTIVE","2"},
        {"MIDZ_HOST_COMPOSE","1"},{"MIDZ_HOST_FUTURE","2"},
        {"MIDZ_HOST_FUTURE_PRESENT","1"},{"MIDZ_DEPTH_MIRROR","2"},
        {"MIDZ_MODEL_ENDPOINT","2"},{"MIDZ_ENDPOINT_EARLY","1"},
        {"MIDZ_ENDPOINT_MARKED","1"}};
    for(const auto &entry:required) {
        const char *value=lookup(entry[0]);
        if(!value || std::strcmp(value,entry[1]))return false;
    }
    policy=DiagnosticJournal::Policy::quiet;return true;
}
}}
