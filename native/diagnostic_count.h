// SPDX-License-Identifier: BSD-3-Clause
// Cumulative diagnostic budgets are distinct from live resource/queue bounds.
#pragma once
#include "diagnostic_journal.h"
#include <cstdint>
#include <limits>

namespace cruisn { namespace diagnostic_count {
inline bool can_add(uint64_t value,uint64_t amount,DiagnosticJournal::Policy policy,
                    uint64_t capture_limit,uint64_t runtime_limit=std::numeric_limits<uint64_t>::max()) {
    if(policy!=DiagnosticJournal::Policy::capture && policy!=DiagnosticJournal::Policy::quiet)return false;
    const uint64_t limit=policy==DiagnosticJournal::Policy::capture?capture_limit:runtime_limit;
    return value<=limit && amount<=limit-value;
}
inline bool add(uint64_t &value,uint64_t amount,DiagnosticJournal::Policy policy,
                uint64_t capture_limit,uint64_t runtime_limit=std::numeric_limits<uint64_t>::max()) {
    if(!can_add(value,amount,policy,capture_limit,runtime_limit))return false;
    value+=amount;return true;
}
}}
